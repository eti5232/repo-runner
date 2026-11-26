"""בדיקות לקלט הריצה ולהודעות השגיאה. לא דורשות Docker."""
import subprocess
from pathlib import Path

import pytest

from reporunner import config, nodes
from reporunner.sandbox import Sandbox
from reporunner.source import SourceError, clone_problem, normalize_source, source_problem


def test_quotes_added_by_windows_copy_as_path_are_removed():
    assert normalize_source('  "C:\\a folder\\x"  ') == "C:\\a folder\\x"


def test_folder_and_url_are_valid(tmp_path: Path):
    assert source_problem(str(tmp_path)) is None
    assert source_problem("https://github.com/user/project") is None


def test_a_file_explains_which_folder_to_give(tmp_path: Path):
    file = tmp_path / "main.py"
    file.write_text("x = 1")
    message = source_problem(str(file))
    assert "קובץ" in message and str(tmp_path) in message


def test_missing_path_and_empty_input_are_reported():
    assert "לא נמצאה" in source_problem("C:/no/such/folder")
    assert source_problem("")


def test_clone_errors_are_translated():
    assert "פרטי" in clone_problem("remote: Repository not found.")
    assert "אינטרנט" in clone_problem("fatal: unable to access: Could not resolve host")


def test_bad_input_fails_before_any_container_is_created(monkeypatch):
    def no_container(*args, **kwargs):
        raise AssertionError("אסור ליצור קונטיינר לקלט שגוי")

    monkeypatch.setattr(nodes, "Sandbox", no_container)
    with pytest.raises(SourceError):
        nodes.clone_repo({"source": "C:/no/such/folder"})


def test_a_hanging_clone_is_stopped_with_a_clear_message(monkeypatch):
    seen = {}

    def hang(command, **kwargs):
        seen.update(kwargs)
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(subprocess, "run", hang)
    box = Sandbox.__new__(Sandbox)  # בלי Docker: רק לוגיקת השכפול
    with pytest.raises(SourceError, match="לא הסתיים"):
        box.clone_project("https://github.com/user/project")
    assert seen["timeout"] == config.CLONE_TIMEOUT_SEC
    assert seen["env"]["GIT_TERMINAL_PROMPT"] == "0"
