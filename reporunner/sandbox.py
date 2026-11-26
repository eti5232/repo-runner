"""ארגז החול: כל העבודה מול Docker.

הסוכן לא מריץ שום דבר על המחשב המארח. כל פקודה של הפרויקט רצה בקונטיינר מבודד,
עם מגבלות זיכרון ו-CPU, כמשתמש רגיל, ובלי גישה לקבצים של המחשב.
"""
import io
import os
import re
import shlex
import ssl
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import uuid
from pathlib import Path

import docker
from docker.models.containers import Container

from reporunner import cancel, config
from reporunner.ignore import skip_label
from reporunner.models import CommandResult
from reporunner.output import clip_output
from reporunner.source import SourceError, clone_problem

CA_BUNDLE = "/etc/ssl/certs/ca-certificates.crt"
TIMEOUT_EXIT_CODE = 124  # קוד היציאה שהפקודה timeout מחזירה כשהזמן נגמר
CHECK_SCRIPT_PATH = f"{config.WORKSPACE}/.rr/check.py"

# סקריפט שרץ *בתוך* הקונטיינר ומריץ את הפרויקט עד שמתברר אם הוא עובד:
#   הסתיים  -> הצלחה אם קוד היציאה 0 (סקריפט רגיל)
#   מאזין לפורט ועונה ב-HTTP בלי שגיאת 5xx -> הצלחה (שרת), ואז עוצרים אותו
#   לא קרה אף אחד מהם בזמן -> כישלון (124)
# כך לא צריך לנחש אם הפרויקט הוא שרת או סקריפט, ולא לנחש את הפורט.
CHECK_SCRIPT = r'''
import os, signal, subprocess, sys, time, urllib.error, urllib.request

command, limit = sys.argv[1], int(sys.argv[2])


def listening_ports():
    ports = set()
    for path in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            for line in open(path).read().splitlines()[1:]:
                parts = line.split()
                if parts[3] == "0A":  # 0A = LISTEN
                    ports.add(int(parts[1].rsplit(":", 1)[1], 16))
        except OSError:
            pass
    return ports


def responds(port):
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=2)
        return True
    except urllib.error.HTTPError as error:
        return error.code < 500  # גם 404 מוכיח ששרת חי
    except Exception:
        return False


log = open("/tmp/rr-check.log", "w+")
proc = subprocess.Popen(command, shell=True, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)


def output():
    log.flush()
    log.seek(0)
    return log.read()


def stop():
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass


deadline = time.time() + limit
while time.time() < deadline:
    code = proc.poll()
    if code is not None:
        print(output())
        sys.exit(code)
    for port in sorted(listening_ports()):
        if responds(port):
            stop()
            print(output())
            print(f"SERVER_OK port {port}")
            sys.exit(0)
    time.sleep(0.5)

stop()
print(output())
print("TIMEOUT: the project neither exited nor answered HTTP", file=sys.stderr)
sys.exit(124)
'''


def host_ca_certificates() -> str:
    """
    1. מקבלת: כלום.
    2. מחזירה: מחרוזת PEM עם תעודות השורש של Windows (ריקה בלינוקס).
    3. עושה: מייצאת את התעודות שהמחשב סומך עליהן, כדי שהקונטיינר יתחבר דרך מסנן כמו NetFree.
    """
    if sys.platform != "win32":
        return ""
    pems = [
        ssl.DER_cert_to_PEM_cert(cert)
        for cert, encoding, _trust in ssl.enum_certificates("ROOT")
        if encoding == "x509_asn"
    ]
    return "".join(pems)


def _tar_bytes(files: dict[str, bytes]) -> bytes:
    """
    1. מקבלת: files: מילון {שם קובץ: תוכן ב-bytes}.
    2. מחזירה: bytes של ארכיון tar.
    3. עושה: אורזת קבצים בזיכרון, כי Docker מקבל קבצים רק כארכיון tar.
    """
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as tar:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


class Sandbox:
    """קונטיינר אחד לריצה אחת של הסוכן."""

    def __init__(self, python_version: str = config.DEFAULT_PYTHON_VERSION, name: str | None = None):
        """
        1. מקבלת: python_version ושם הקונטיינר (לא חובה).
        2. מחזירה: כלום.
        3. עושה: שומרת את ההגדרות ומתחברת ל-Docker. הקונטיינר עצמו עדיין לא נוצר.
        """
        self.python_version = python_version
        self.name = name or f"reporunner-{uuid.uuid4().hex[:8]}"
        self.client = docker.from_env()
        self.container: Container | None = None

    @classmethod
    def attach(cls, name: str) -> "Sandbox":
        """
        1. מקבלת: name: שם קונטיינר שכבר רץ.
        2. מחזירה: Sandbox מחובר אליו.
        3. עושה: מאפשרת לכל צומת להתחבר מחדש לקונטיינר, כי ב-State נשמר רק השם.
        """
        box = cls(name=name)
        box.container = box.client.containers.get(name)
        return box

    # ---------- מחזור חיים ----------

    def start(self) -> None:
        """
        1. מקבלת: כלום.
        2. מחזירה: כלום.
        3. עושה: יוצרת קונטיינר מבודד (זיכרון ו-CPU מוגבלים, cache משותף ל-pip) ומכינה אותו. אם ההכנה נכשלת מוחקת אותו.
        """
        image = f"python:{self.python_version}-slim"
        try:
            self.client.images.get(image)
        except docker.errors.ImageNotFound:
            self.client.images.pull(image)

        thread_id = cancel.current_thread_id()
        self.container = self.client.containers.run(
            image,
            labels={cancel.THREAD_LABEL: thread_id} if thread_id else {},  # לפי הסימון מוחקים כשעוצרים ריצה
            command=["sleep", "infinity"],  # הקונטיינר רק "חי"; את הפקודות שולחים אליו עם exec
            name=self.name,
            detach=True,
            mem_limit=config.MEMORY_LIMIT,
            nano_cpus=int(config.CPU_LIMIT * 1e9),
            # שני פורטים מועברים למחשב המארח (פורט אקראי פנוי), כדי שתצוגה חיה תיפתח בדפדפן: שרת הפרויקט ו-noVNC
            # רק 127.0.0.1: התצוגה נגישה מהמחשב הזה בלבד, ולא לכל מי שנמצא איתו ברשת (noVNC רץ בלי סיסמה)
            ports={f"{config.PREVIEW_WEB_PORT}/tcp": ("127.0.0.1", None), f"{config.VNC_WEB_PORT}/tcp": ("127.0.0.1", None)},
            volumes={config.PIP_CACHE_VOLUME: {"bind": f"/home/{config.CONTAINER_USER}/.cache/pip", "mode": "rw"}},
            environment={
                # כל הכלים בקונטיינר יסמכו על מאגר התעודות המעודכן (כולל NetFree)
                "PIP_CERT": CA_BUNDLE,
                "REQUESTS_CA_BUNDLE": CA_BUNDLE,
                "SSL_CERT_FILE": CA_BUNDLE,
                "GIT_SSL_CAINFO": CA_BUNDLE,
                # python ו-pip יעבדו מתוך הסביבה הווירטואלית
                "VIRTUAL_ENV": config.VENV_DIR,
                "PATH": f"{config.VENV_DIR}/bin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
                "PIP_DISABLE_PIP_VERSION_CHECK": "1",
                "PYTHONUNBUFFERED": "1",
            },
        )
        try:
            self._prepare()
        except Exception:
            # אם ההכנה נכשלה, __exit__ לא ייקרא (כי __enter__ לא הסתיים) – מנקים כאן, אחרת הקונטיינר נשאר יתום
            self.stop()
            raise

    def _prepare(self) -> None:
        """
        1. מקבלת: כלום.
        2. מחזירה: כלום.
        3. עושה: כ-root: יוצרת משתמש רגיל, תיקיות ותעודות. אחר כך כמשתמש הרגיל: סביבה וירטואלית.
        """
        user = config.CONTAINER_USER
        certs = host_ca_certificates()
        if certs:
            self.container.put_archive("/usr/local/share/ca-certificates", _tar_bytes({"host-roots.crt": certs.encode()}))
        setup = (
            f"useradd --create-home {user} && "
            f"mkdir -p {config.WORKSPACE} {config.SECRETS_DIR} {config.WORKSPACE}/.rr && "
            f"chown -R {user}:{user} {config.WORKSPACE} /home/{user} && "
            "update-ca-certificates > /dev/null 2>&1"
        )
        self._must(self.run(setup, user="root", workdir="/"))  # /workspace עוד לא קיימת
        self._must(self.run(f"python -m venv {config.VENV_DIR}"))

    def stop(self) -> None:
        """
        1. מקבלת: כלום.
        2. מחזירה: כלום.
        3. עושה: מוחקת את הקונטיינר. ה-volume של ה-cache נשאר לריצה הבאה.
        """
        if self.container is not None:
            try:
                self.container.remove(force=True)
            except docker.errors.NotFound:  # כבר נמחק, למשל בעצירת הריצה
                pass
            self.container = None

    def stop_later(self, seconds: float) -> None:
        """
        1. מקבלת: seconds (אחרי כמה זמן לסגור).
        2. מחזירה: כלום.
        3. עושה: מתזמנת מחיקה של הקונטיינר, כדי שתצוגה חיה שנשכחה לא תישאר פעילה לנצח.
        """
        timer = threading.Timer(seconds, self.stop)
        timer.daemon = True
        timer.start()

    def __enter__(self) -> "Sandbox":
        """
        1. מקבלת: כלום.
        2. מחזירה: ה-Sandbox עצמו.
        3. עושה: מאפשרת כתיבה של with Sandbox() as box: יוצרת את הקונטיינר בכניסה.
        """
        self.start()
        return self

    def __exit__(self, *exc) -> None:
        """
        1. מקבלת: פרטי חריגה (לא בשימוש).
        2. מחזירה: כלום.
        3. עושה: מוחקת את הקונטיינר ביציאה מבלוק ה-with, גם אם הייתה שגיאה.
        """
        self.stop()

    # ---------- הפרויקט ----------

    def copy_project(self, source: Path) -> list[str]:
        """
        1. מקבלת: source: תיקייה מקומית.
        2. מחזירה: רשימת הנתיבים שלא הועתקו (סביבות וירטואליות, git, קבצי סודות), ממויינת.
        3. עושה: מעתיקה את הפרויקט לקונטיינר ומעבירה בעלות למשתמש הרגיל. מדלגת על מה ש-reporunner/ignore.py קובע.
        """
        skipped: list[str] = []

        def keep(entry: tarfile.TarInfo) -> tarfile.TarInfo | None:
            """מחליטה לגבי פריט אחד בארכיון: מחזירה אותו, או None כדי לדלג (תיקייה שדולגה לא נסרקת בכלל)."""
            relative = entry.name.removeprefix("repo/")
            if relative != "repo" and skip_label(relative.rsplit("/", 1)[-1], entry.isdir()):
                skipped.append(relative)
                return None
            return entry

        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w") as tar:
            tar.add(source, arcname="repo", filter=keep)
        self.container.put_archive(config.WORKSPACE, buffer.getvalue())
        # הקבצים הועתקו כ-root – מעבירים בעלות למשתמש הרגיל
        self._must(self.run(f"chown -R {config.CONTAINER_USER}:{config.CONTAINER_USER} {config.REPO_DIR}", user="root"))
        return sorted(skipped)

    def clone_project(self, url: str, commit: str | None = None) -> None:
        """
        1. מקבלת: url ו-commit (לא חובה).
        2. מחזירה: כלום.
        3. עושה: משכפלת את הפרויקט במחשב המארח (בתמונה אין git), נועלת ל-commit אם צוין, ומעתיקה לקונטיינר.
           עם מגבלת זמן ובלי חלונות התחברות, כדי ששכפול לא יישאר תקוע. כשל מדווח כ-SourceError עם הסבר.
        """
        # בלי זה Git ב-Windows עלול לפתוח חלון התחברות ולחכות לנצח
        environment = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"}
        depth = [] if commit else ["--depth", "1"]  # בלי commit מסוים אין צורך בהיסטוריה, וזה מהיר בהרבה

        def git(*arguments: str) -> None:
            """מריצה פקודת git אחת עם מגבלת הזמן."""
            try:
                subprocess.run(["git", *arguments], check=True, capture_output=True, env=environment,
                               stdin=subprocess.DEVNULL, timeout=config.CLONE_TIMEOUT_SEC)
            except subprocess.TimeoutExpired as error:
                raise SourceError(f"השכפול לא הסתיים בתוך {config.CLONE_TIMEOUT_SEC} שניות. ייתכן שהריפו גדול מאוד "
                                  "או שהרשת איטית. אפשר להוריד אותו ולתת תיקייה.") from error
            except subprocess.CalledProcessError as error:
                raise SourceError(clone_problem(error.stderr.decode(errors="replace"))) from error

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            target = Path(tmp) / "repo"
            git("clone", "--quiet", *depth, url, str(target))
            if commit:
                git("-C", str(target), "checkout", "--quiet", commit)
            self.copy_project(target)

    def copy_state_to(self, other: "Sandbox") -> None:
        """
        1. מקבלת: other: Sandbox אחר.
        2. מחזירה: כלום.
        3. עושה: מעתיקה אליו את הפרויקט (כולל תיקונים) ואת הסודות; משמשת במעבר בין גרסאות Python.
        """
        for path in (config.REPO_DIR, config.SECRETS_DIR):
            chunks, _stat = self.container.get_archive(path)
            other.container.put_archive(str(Path(path).parent.as_posix()), b"".join(chunks))
        owner = f"{config.CONTAINER_USER}:{config.CONTAINER_USER}"
        other._must(other.run(f"chown -R {owner} {config.REPO_DIR} {config.SECRETS_DIR}", user="root", workdir="/"))

    # ---------- סודות ----------

    def set_secret(self, name: str, value: str) -> None:
        """
        1. מקבלת: name (שם משתנה סביבה) ו-value (הערך).
        2. מחזירה: כלום.
        3. עושה: שומרת סוד בקונטיינר בלבד, כקובץ, ומעכשיו כל פקודה תראה אותו.
        הערה: הערך לא עובר בשורת פקודה, וגם לא ב-State, ב-checkpointer או ב-LangSmith.
        """
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ValueError(f"שם משתנה לא תקין: {name!r}")
        self.container.put_archive(config.SECRETS_DIR, _tar_bytes({name: value.encode()}))
        owner = f"{config.CONTAINER_USER}:{config.CONTAINER_USER}"
        self._must(self.run(f"chown {owner} {config.SECRETS_DIR}/{name} && chmod 600 {config.SECRETS_DIR}/{name}", user="root", workdir="/"))

    # ---------- הרצת פקודות ----------

    def run(
        self,
        command: str,
        timeout: int = config.COMMAND_TIMEOUT_SEC,
        user: str = config.CONTAINER_USER,
        workdir: str | None = None,
    ) -> CommandResult:
        """
        1. מקבלת: command, timeout, user (ברירת מחדל: משתמש רגיל), workdir (לא חובה).
        2. מחזירה: CommandResult: קוד יציאה, stdout, stderr, חריגת זמן ומשך.
        3. עושה: מריצה פקודת shell בקונטיינר עם הגבלת זמן, אחרי טעינת הסודות. פלט ארוך מקוצר.
        הערה: ל-Docker אין timeout ל-exec, ולכן עוטפים בפקודת timeout של לינוקס (קוד 124).
        """
        if workdir is None:  # ברירת מחדל: תיקיית הפרויקט, ואם עוד לא הועתק – תיקיית העבודה
            workdir = config.REPO_DIR if self._repo_exists() else config.WORKSPACE
        # לפני כל פקודה טוענים את הסודות שהמשתמש סיפק (קובץ לכל משתנה, שם הקובץ = שם המשתנה)
        load_secrets = (
            f'for f in {config.SECRETS_DIR}/*; do [ -f "$f" ] && export "$(basename "$f")=$(cat "$f")"; done; '
        )
        wrapped = ["timeout", str(timeout), "sh", "-c", load_secrets + command]
        started = time.monotonic()
        exit_code, (out, err) = self.container.exec_run(wrapped, user=user, workdir=workdir, demux=True)
        return CommandResult(
            command=command,
            exit_code=exit_code,
            stdout=clip_output((out or b"").decode(errors="replace"), config.OUTPUT_LIMIT_CHARS),
            stderr=clip_output((err or b"").decode(errors="replace"), config.OUTPUT_LIMIT_CHARS),
            timed_out=exit_code == TIMEOUT_EXIT_CODE,
            duration_sec=round(time.monotonic() - started, 2),
        )

    def host_port(self, container_port: int) -> int:
        """
        1. מקבלת: container_port (פורט בתוך הקונטיינר שהועבר למארח).
        2. מחזירה: מספר הפורט במחשב המארח.
        3. עושה: קוראת מ-Docker לאיזה פורט במארח מופה הפורט (Docker בוחר פורט פנוי אקראי).
        """
        self.container.reload()
        bindings = self.container.attrs["NetworkSettings"]["Ports"].get(f"{container_port}/tcp")
        if not bindings:
            raise RuntimeError(f"הפורט {container_port} לא מועבר למארח")
        return int(bindings[0]["HostPort"])

    def read_bytes(self, path: str) -> bytes:
        """
        1. מקבלת: path (נתיב מוחלט של קובץ בקונטיינר).
        2. מחזירה: תוכן הקובץ (bytes).
        3. עושה: מעתיקה קובץ מהקונטיינר, למשל הקלטת וידאו, דרך ארכיון tar שDocker מחזיר.
        """
        stream, _ = self.container.get_archive(path)
        archive = io.BytesIO(b"".join(stream))
        with tarfile.open(fileobj=archive) as tar:
            member = tar.getmembers()[0]
            return tar.extractfile(member).read()

    def write_text(self, path: str, content: str) -> None:
        """
        1. מקבלת: path (נתיב מוחלט בקונטיינר) ו-content (טקסט).
        2. מחזירה: כלום.
        3. עושה: כותבת קובץ טקסט בקונטיינר, כדי להכניס אליו סקריפטי עזר.
        """
        folder, _, name = path.rpartition("/")
        self.container.put_archive(folder or "/", _tar_bytes({name: content.encode()}))

    def run_checked(self, command: str, timeout: int = config.RUN_CHECK_TIMEOUT) -> CommandResult:
        """
        1. מקבלת: command ו-timeout.
        2. מחזירה: CommandResult, ובשרת שענה: ב-stdout השורה 'SERVER_OK port N'.
        3. עושה: מריצה את הפרויקט ומחכה: הסתיים בקוד 0 או שרת שעונה ב-HTTP הם הצלחה; כל השאר כישלון.
        """
        self.container.put_archive(f"{config.WORKSPACE}/.rr", _tar_bytes({"check.py": CHECK_SCRIPT.encode()}))
        wrapped = f"python {CHECK_SCRIPT_PATH} {shlex.quote(command)} {timeout}"
        result = self.run(wrapped, timeout=timeout + 15)
        # ב-CommandResult מציגים את הפקודה של הפרויקט, לא את פקודת העטיפה
        return result.model_copy(update={"command": command})

    def _repo_exists(self) -> bool:
        """
        1. מקבלת: כלום.
        2. מחזירה: bool.
        3. עושה: בודקת אם תיקיית הפרויקט כבר קיימת בקונטיינר (לקביעת תיקיית העבודה).
        """
        exit_code, _ = self.container.exec_run(["test", "-d", config.REPO_DIR])
        return exit_code == 0

    @staticmethod
    def _must(result: CommandResult) -> None:
        """
        1. מקבלת: result (CommandResult).
        2. מחזירה: כלום.
        3. עושה: פקודות הכנה חייבות להצליח: אם נכשלה, זורקת RuntimeError עם השגיאה.
        """
        if not result.ok:
            raise RuntimeError(f"הכנת הקונטיינר נכשלה: {shlex.quote(result.command)}\n{result.stderr}")
