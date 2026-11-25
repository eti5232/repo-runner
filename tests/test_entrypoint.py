"""בדיקות לזיהוי נקודת הכניסה ולסינון ההעתקה. לא דורשות Docker."""
import tarfile
from pathlib import Path

from reporunner import entrypoint
from reporunner.ignore import skip_label
from reporunner.models import ProjectProfile


# ---------- בחירת קובץ ----------

def test_known_name_wins_when_nothing_else_is_special():
    assert entrypoint.pick({"main.py", "utils.py"}, {}, []) == ("main.py", None)


def test_known_names_keep_their_order():
    assert entrypoint.pick({"cli.py", "app.py"}, {}, [])[0] == "app.py"


def test_single_file_with_main_guard_is_found():
    assert entrypoint.pick({"minesweeper.py"}, {}, ["minesweeper.py"]) == ("minesweeper.py", None)


def test_among_many_main_files_the_app_like_name_is_chosen():
    files = ["add_pages.py", "build_index.py", "chat_app.py", "run_tests.py", "query.py"]
    assert entrypoint.choose(files) == "chat_app.py"


def test_nothing_found_returns_none():
    assert entrypoint.pick({"README.md"}, {}, []) == (None, None)


# ---------- מסגרות ----------

def test_chainlit_project_runs_with_chainlit_not_python():
    entry, command = entrypoint.pick({"chat_app.py", "build_index.py"}, {"chainlit": ["chat_app.py"]}, ["build_index.py"])
    assert entry == "chat_app.py"
    assert command == "chainlit run chat_app.py --headless"


def test_streamlit_project_runs_with_streamlit():
    entry, command = entrypoint.pick({"app.py"}, {"streamlit": ["app.py"]}, [])
    assert (entry, command) == ("app.py", "streamlit run app.py --server.headless true")


def test_file_names_with_spaces_are_quoted_in_the_command():
    profile = ProjectProfile(python_version="3.12", deps_file=None, has_tests=False, entrypoint="Snake Game.py")
    assert entrypoint.run_command_of(profile) == "python 'Snake Game.py'"


def test_explicit_run_command_beats_python_file():
    profile = ProjectProfile(python_version="3.12", deps_file=None, has_tests=False, entrypoint="app.py",
                             run_command="streamlit run app.py")
    assert entrypoint.run_command_of(profile) == "streamlit run app.py"


def test_no_entrypoint_gives_no_command():
    assert entrypoint.run_command_of(ProjectProfile(python_version="3.12", deps_file=None, has_tests=False, entrypoint=None)) is None


class FakeBox:
    """מחליף את הקונטיינר: מחזיר פלט grep קבוע."""

    def __init__(self, framework_hits: str, main_files: str):
        self.outputs = [framework_hits, main_files]

    def run(self, command, **kwargs):
        from types import SimpleNamespace
        return SimpleNamespace(stdout=self.outputs.pop(0))


def test_detect_reads_grep_output_and_ignores_deep_files():
    box = FakeBox("./chat_app.py:import chainlit\n./deep/a/b/other.py:import chainlit\n", "build_index.py\nchat_app.py\n")
    assert entrypoint.detect(box, {"chat_app.py", "build_index.py"}) == ("chat_app.py", "chainlit run chat_app.py --headless")


# ---------- סינון העתקה ----------

def test_heavy_and_useless_folders_are_skipped():
    for name in (".venv", ".git", "node_modules", "__pycache__", ".idea"):
        assert skip_label(name, is_dir=True) == name


def test_secret_files_are_skipped_but_templates_are_kept():
    assert skip_label(".env", is_dir=False) == ".env"
    assert skip_label(".env.local", is_dir=False) == ".env.local"
    assert skip_label("server.pem", is_dir=False)
    assert skip_label(".env.example", is_dir=False) is None
    assert skip_label("main.py", is_dir=False) is None


def test_a_normal_data_folder_is_not_skipped():
    assert skip_label("chroma_db", is_dir=True) is None
    assert skip_label("data", is_dir=True) is None


def test_copy_filter_skips_without_descending(tmp_path: Path):
    """בדיקה על הלוגיקה של המסנן בארכיון אמיתי, בלי Docker."""
    (tmp_path / ".venv" / "lib").mkdir(parents=True)
    (tmp_path / ".venv" / "lib" / "big.bin").write_text("x")
    (tmp_path / ".env").write_text("KEY=secret")
    (tmp_path / "main.py").write_text("print(1)")
    skipped: list[str] = []

    def keep(entry: tarfile.TarInfo):
        relative = entry.name.removeprefix("repo/")
        if relative != "repo" and skip_label(relative.rsplit("/", 1)[-1], entry.isdir()):
            skipped.append(relative)
            return None
        return entry

    import io
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as tar:
        tar.add(tmp_path, arcname="repo", filter=keep)
    names = tarfile.open(fileobj=io.BytesIO(buffer.getvalue())).getnames()
    assert "repo/main.py" in names
    assert not any(".venv" in name or name.endswith(".env") for name in names)
    assert sorted(skipped) == [".env", ".venv"]
