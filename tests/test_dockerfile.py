"""הבדיקה שסוגרת את M5: ה-Dockerfile שהסוכן מייצר באמת נבנה ורץ בפני עצמו.

הבדיקה רצה על פרויקט תקין (בלי מודל שפה), בונה image עם `docker build` אמיתי, ומריצה אותו.
אורכת כדקה, כי יש בה build והתקנת חבילה.

הרצה:  python -m pytest tests/test_dockerfile.py -v
"""
import shutil
import subprocess
from pathlib import Path

import docker
import pytest

from reporunner.graph import graph
from reporunner.sandbox import host_ca_certificates

FIXTURE = Path(__file__).resolve().parent.parent / "evaluation" / "fixtures" / "ok_requests_script"
IMAGE = "reporunner-test-image"


def _docker_available() -> bool:
    try:
        docker.from_env().ping()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _docker_available(), reason="Docker לא פועל")


def _trust_host_certificates(dockerfile: str, context: Path) -> str:
    """ברשת עם מסנן (כמו NetFree) גם build ב-Docker צריך להכיר את התעודה שלו. מוסיפים אותה רק לצורך הבדיקה.

    ה-Dockerfile שהסוכן מייצר נשאר נקי ונייד: על מחשב בלי מסנן אין צורך בשורות האלה.
    """
    certs = host_ca_certificates()
    if not certs:
        return dockerfile
    (context / "host-roots.crt").write_text(certs)
    extra = ["COPY host-roots.crt /usr/local/share/ca-certificates/host-roots.crt",
             "RUN update-ca-certificates",
             "ENV PIP_CERT=/etc/ssl/certs/ca-certificates.crt"]
    lines = dockerfile.splitlines()
    index = next(i for i, line in enumerate(lines) if line.startswith("FROM "))
    return "\n".join(lines[: index + 1] + extra + lines[index + 1:]) + "\n"


def test_generated_dockerfile_builds_and_runs(tmp_path):
    result = graph.invoke({"source": str(FIXTURE)})
    report = result["report"]
    assert report.succeeded

    context = tmp_path / "ctx"
    shutil.copytree(FIXTURE, context)
    (context / "Dockerfile").write_text(_trust_host_certificates(report.dockerfile, context), newline="\n")

    try:
        build = subprocess.run(["docker", "build", "-t", IMAGE, str(context)], capture_output=True, text=True, timeout=300)
        assert build.returncode == 0, build.stderr[-1500:]
        run = subprocess.run(["docker", "run", "--rm", IMAGE], capture_output=True, text=True, timeout=60)
        assert run.returncode == 0, run.stderr
        assert "requests 2.32.3 is installed" in run.stdout
    finally:
        subprocess.run(["docker", "rmi", "-f", IMAGE], capture_output=True)
