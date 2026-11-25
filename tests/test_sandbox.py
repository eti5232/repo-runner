"""בדיקות אינטגרציה לארגז החול. דורשות Docker פועל.

הרצה מתיקיית הפרויקט:  python -m pytest tests/test_sandbox.py -v
"""
import docker
import pytest

from reporunner.sandbox import Sandbox


def _docker_available() -> bool:
    try:
        docker.from_env().ping()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _docker_available(), reason="Docker לא פועל")


@pytest.fixture(scope="module")
def sandbox():
    """קונטיינר אחד לכל הבדיקות בקובץ – יצירה שלו לוקחת כמה שניות."""
    with Sandbox(python_version="3.12") as box:
        yield box


def test_python_version(sandbox):
    result = sandbox.run("python --version")
    assert result.ok
    assert "3.12" in result.stdout


def test_runs_as_regular_user(sandbox):
    assert sandbox.run("whoami").stdout.strip() == "runner"


def test_pip_install_works_behind_netfree(sandbox):
    """בודק בבת אחת: תעודות NetFree, הסביבה הווירטואלית וה-cache."""
    result = sandbox.run("pip install --quiet requests && python -c 'import requests'")
    assert result.ok, result.stderr


def test_timeout(sandbox):
    result = sandbox.run("sleep 5", timeout=1)
    assert result.timed_out
    assert not result.ok


def test_run_checked_script_that_exits_successfully(sandbox, tmp_path):
    (tmp_path / "hello.py").write_text("print('done')")
    sandbox.copy_project(tmp_path)
    result = sandbox.run_checked("python hello.py", timeout=20)
    assert result.ok and "done" in result.stdout


def test_run_checked_script_that_fails_keeps_its_error_output(sandbox, tmp_path):
    (tmp_path / "bad.py").write_text("raise SystemExit('boom')")
    sandbox.copy_project(tmp_path)
    result = sandbox.run_checked("python bad.py", timeout=20)
    assert not result.ok and "boom" in result.stdout


def test_run_checked_detects_a_server_and_its_port(sandbox, tmp_path):
    """שרת לא מסתיים לבד. הוא נחשב עובד כי הוא עונה ב-HTTP, והפורט נלמד בלי שמישהו ציין אותו."""
    sandbox.copy_project(tmp_path)
    result = sandbox.run_checked("python -m http.server 8765", timeout=30)
    assert result.ok
    assert "SERVER_OK port 8765" in result.stdout


def test_copy_project_and_run(sandbox, tmp_path):
    (tmp_path / "hello.py").write_text("print('hello from the sandbox')")
    sandbox.copy_project(tmp_path)
    result = sandbox.run("python hello.py")
    assert result.ok
    assert result.stdout.strip() == "hello from the sandbox"
