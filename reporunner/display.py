"""מסך וירטואלי בקונטיינר: מאפשר להריץ פרויקט עם חלון, ולראות אותו בדפדפן (noVNC) או להקליט אותו.

התקנת הכלים והפעלתם נעשות בקוד (לא ע"י המודל), ולכן הן לא עוברות בשער הבטיחות של תיקונים.
כל הפונקציות מקבלות Sandbox ועובדות בתוך הקונטיינר שלו.
"""
import re
from pathlib import Path

from reporunner import config
from reporunner.models import CommandResult
from reporunner.sandbox import Sandbox

# ייבוא של ספריית חלונות בקוד של הפרויקט
GUI_IMPORT = r"^[[:space:]]*(import|from)[[:space:]]+(tkinter|Tkinter|pygame|PyQt5|PyQt6|PySide2|PySide6|wx|kivy|turtle)\b"

# חבילות המערכת, בשלוש קבוצות. מתקינים רק מה שצריך, כי כל חבילה היא הורדה (דקות ברשת איטית):
BASE_PACKAGES = {"xvfb": "Xvfb", "libtk8.6": None, "x11-utils": "xwininfo"}          # מסך וירטואלי, tkinter, זיהוי חלונות
LIVE_PACKAGES = {"x11vnc": "x11vnc", "novnc": None, "websockify": "websockify"}      # רק לתצוגה חיה בדפדפן
RECORDING_PACKAGES = {"ffmpeg": "ffmpeg"}                                            # רק להקלטה

RECORDING_FILE = "/tmp/rr-recording.mp4"
CHECK_TIMEOUT_EXIT = 124  # קוד היציאה של בדיקת ההצלחה כשהפרויקט לא הסתיים ולא ענה ב-HTTP בזמן

# מעביר תנועה: מקשיב על 0.0.0.0 בפורט שמועבר למארח, ומעביר לשרת של הפרויקט (שלעיתים מקשיב רק על 127.0.0.1)
FORWARDER = r'''
import socket, sys, threading

listen_port, target_port = int(sys.argv[1]), int(sys.argv[2])


def pipe(source, target):
    try:
        while data := source.recv(65536):
            target.sendall(data)
    except OSError:
        pass
    finally:
        for side in (source, target):
            try:
                side.close()
            except OSError:
                pass


def handle(client):
    try:
        upstream = socket.create_connection(("127.0.0.1", target_port))
    except OSError:
        client.close()
        return
    threading.Thread(target=pipe, args=(client, upstream), daemon=True).start()
    threading.Thread(target=pipe, args=(upstream, client), daemon=True).start()


server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("0.0.0.0", listen_port))
server.listen(50)
while True:
    connection, _ = server.accept()
    handle(connection)
'''
FORWARDER_PATH = f"{config.WORKSPACE}/.rr/forward.py"


def detect_gui(box: Sandbox) -> bool:
    """
    1. מקבלת: box (קונטיינר עם הפרויקט).
    2. מחזירה: True אם הפרויקט מייבא ספריית חלונות.
    3. עושה: מחפשת בקבצי הפייתון של הפרויקט ייבוא של tkinter, pygame, Qt וכדומה.
    """
    result = box.run(f"grep -rEl --include='*.py' '{GUI_IMPORT}' . | head -1")
    return bool(result.stdout.strip())


def count_windows(tree_output: str) -> int:
    """
    1. מקבלת: tree_output (הפלט של xwininfo -root -tree).
    2. מחזירה: כמה חלונות פתוחים על המסך.
    3. עושה: סופרת את שורות החלונות בעץ (כל שורה שמתחילה במזהה חלון כמו 0x400001), ולא את חלון השורש.
    """
    return len(re.findall(r"^\s+0x[0-9a-fA-F]+ ", tree_output, re.MULTILINE))


def opens_window(box: Sandbox, command: str) -> bool:
    """
    1. מקבלת: box (עם מסך וירטואלי רץ) ו-command (פקודה של הפרויקט).
    2. מחזירה: True אם הפקודה פתחה חלון על המסך הווירטואלי.
    3. עושה: מריצה את הפקודה ברקע, ממתינה כמה שניות, בודקת אם נפתח חלון, וסוגרת אותה. כך מבדילים פקודת חלון
       (למשל learn) מפקודה שרק רצה זמן רב בלי חלון (למשל train).
    """
    wait = config.WINDOW_WAIT_SEC
    script = (f"env DISPLAY={config.DISPLAY} {command} > /dev/null 2>&1 & pid=$!; sleep {wait}; "
              f"xwininfo -display {config.DISPLAY} -root -tree; kill $pid 2>/dev/null; exit 0")
    result = box.run(script, timeout=wait + 20)
    return count_windows(result.stdout) > 0


def run_gui_check(box: Sandbox, command: str) -> CommandResult:
    """
    1. מקבלת: box ו-command (פקודה שמריצה פרויקט עם חלון).
    2. מחזירה: CommandResult: הצלחה (קוד 0) אם נפתח חלון, אחרת התוצאה האמיתית של ההרצה.
    3. עושה: מכינה מסך וירטואלי, מריצה את הפרויקט עליו ובודקת אם הוא נשאר חי ופתח חלון. חלון שנשאר פתוח הוא הצלחה,
       בניגוד לסקריפט רגיל שמצפים שיסתיים. אם ההתקנה נכשלה, מחזירה את הכשל שלה.
    """
    install = install_display_stack(box)
    if not install.ok:
        return install
    start_display(box)
    result = box.run_checked(f"env DISPLAY={config.DISPLAY} {command}", timeout=config.GUI_CHECK_TIMEOUT_SEC)
    result = result.model_copy(update={"command": command})
    if result.exit_code == CHECK_TIMEOUT_EXIT and opens_window(box, command):
        return result.model_copy(update={"exit_code": 0, "stderr": "", "timed_out": False})
    return result


def _background(box: Sandbox, command: str, log: str) -> CommandResult:
    """
    1. מקבלת: box, command (פקודה שנשארת רצה) ו-log (קובץ לפלט שלה).
    2. מחזירה: CommandResult של ההפעלה (לא של הפקודה עצמה).
    3. עושה: מפעילה פקודה ברקע, מנותקת מה-exec, כך שהיא ממשיכה לרוץ אחרי שהקריאה חוזרת.
    """
    return box.run(f"setsid nohup {command} > {log} 2>&1 < /dev/null &", timeout=20)


def install_display_stack(box: Sandbox, live: bool = False, recording: bool = False) -> CommandResult:
    """
    1. מקבלת: box, live (האם גם להתקין את כלי התצוגה החיה בדפדפן) ו-recording (האם גם כלי הקלטה).
    2. מחזירה: CommandResult של ההתקנה.
    3. עושה: מתקינה כ-root את החבילות הדרושות בלבד: בסיס (מסך וירטואלי וזיהוי חלונות) תמיד, ובנוסף רק מה שהמשתמשת
       בחרה. חבילות שכבר מותקנות לא יורדות שוב.
    """
    groups = [BASE_PACKAGES] + ([LIVE_PACKAGES] if live else []) + ([RECORDING_PACKAGES] if recording else [])
    packages = {name: tool for group in groups for name, tool in group.items()}
    tools = [tool for tool in packages.values() if tool]  # פקודות שאפשר לבדוק אם קיימות; לספריות בלי פקודה לא בודקים
    check = " && ".join(f"command -v {tool} > /dev/null" for tool in tools)
    install = ("apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends "
               + " ".join(packages))
    return box.run(f"({check}) || ({install})", user="root", workdir="/", timeout=600)



def start_display(box: Sandbox) -> None:
    """
    1. מקבלת: box (עם החבילות מותקנות).
    2. מחזירה: כלום.
    3. עושה: מפעילה מסך וירטואלי (Xvfb), אם עדיין לא רץ.
    """
    box.run(f"pgrep -x Xvfb > /dev/null || {_start_xvfb_command()}", timeout=20)
    box.run("sleep 1", timeout=10)


def _start_xvfb_command() -> str:
    """
    1. מקבלת: כלום.
    2. מחזירה: פקודת shell שמפעילה Xvfb ברקע.
    3. עושה: בונה את פקודת ההפעלה לפי הגדרות המסך.
    """
    return f"(setsid nohup Xvfb {config.DISPLAY} -screen 0 {config.SCREEN_SIZE} > /tmp/rr-xvfb.log 2>&1 < /dev/null &)"


def start_vnc(box: Sandbox) -> int:
    """
    1. מקבלת: box (עם מסך וירטואלי רץ).
    2. מחזירה: הפורט במחשב המארח שבו noVNC זמין.
    3. עושה: מפעילה שרת VNC על המסך, וגשר שמגיש אותו לדפדפן דרך noVNC.
    """
    box.run(f"pgrep -x x11vnc > /dev/null || (setsid nohup x11vnc -display {config.DISPLAY} -forever -shared -nopw "
            f"-rfbport 5900 -quiet > /tmp/rr-vnc.log 2>&1 < /dev/null &)", timeout=20)
    box.run(f"pgrep -f websockify > /dev/null || (setsid nohup websockify --web /usr/share/novnc "
            f"{config.VNC_WEB_PORT} localhost:5900 > /tmp/rr-ws.log 2>&1 < /dev/null &)", timeout=20)
    box.run("sleep 1", timeout=10)
    return box.host_port(config.VNC_WEB_PORT)


def launch_gui(box: Sandbox, command: str) -> None:
    """
    1. מקבלת: box ו-command (פקודה שפותחת חלון).
    2. מחזירה: כלום.
    3. עושה: מפעילה את הפרויקט ברקע על המסך הווירטואלי, בתוך תיקיית הפרויקט.
    """
    _background(box, f"env DISPLAY={config.DISPLAY} {command}", "/tmp/rr-app.log")


def desktop_url(host_port: int) -> str:
    """
    1. מקבלת: host_port (הפורט של noVNC במארח).
    2. מחזירה: כתובת URL שפותחת את החלון בדפדפן.
    3. עושה: בונה כתובת שמתחברת אוטומטית ומתאימה את גודל החלון.
    """
    return f"http://localhost:{host_port}/vnc.html?autoconnect=1&resize=scale&reconnect=1"


def launch_web(box: Sandbox, command: str, app_port: int) -> int:
    """
    1. מקבלת: box, command (פקודה שמפעילה שרת) ו-app_port (הפורט שבו השרת מקשיב בקונטיינר).
    2. מחזירה: הפורט במחשב המארח שבו אפשר לגלוש לשרת.
    3. עושה: מפעילה את השרת ברקע ומעבירה אליו תנועה מהפורט המועבר למארח, גם אם הוא מקשיב רק על 127.0.0.1.
    """
    box.write_text(FORWARDER_PATH, FORWARDER)
    _background(box, command, "/tmp/rr-app.log")
    _background(box, f"python {FORWARDER_PATH} {config.PREVIEW_WEB_PORT} {app_port}", "/tmp/rr-forward.log")
    box.run("sleep 2", timeout=10)
    return box.host_port(config.PREVIEW_WEB_PORT)


def record(box: Sandbox, container_name: str) -> Path:
    """
    1. מקבלת: box (עם המסך והחלון רצים) ו-container_name.
    2. מחזירה: הנתיב בשרת של קובץ ההקלטה (mp4).
    3. עושה: מקליטה את המסך הווירטואלי כמה שניות, ומעתיקה את הקובץ למחשב המארח, כך שהקונטיינר יכול להיסגר.
    """
    seconds = config.RECORD_SECONDS
    size = config.SCREEN_SIZE.rsplit("x", 1)[0]
    box.run(f"ffmpeg -y -loglevel error -f x11grab -video_size {size} -framerate 15 -i {config.DISPLAY} "
            f"-t {seconds} -pix_fmt yuv420p {RECORDING_FILE}", timeout=seconds + 30)
    target = recording_path(container_name)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(box.read_bytes(RECORDING_FILE))
    return target


def recording_path(container_name: str) -> Path:
    """
    1. מקבלת: container_name (שם הקונטיינר של הריצה).
    2. מחזירה: הנתיב של קובץ ההקלטה במחשב המארח.
    3. עושה: מגדירה איפה שומרים הקלטה: בתיקיית הריצה, לפי שם הקונטיינר.
    """
    safe = re.sub(r"[^A-Za-z0-9_-]", "", container_name)
    return config.RUNS_DIR / safe / "recording.mp4"
