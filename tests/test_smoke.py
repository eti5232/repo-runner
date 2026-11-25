"""בדיקות לבדיקת הפקודות ולהכנת התצוגה. לא דורשות Docker."""
from reporunner import display, nodes_preview, smoke
from reporunner.graph import route_after_smoke, route_after_verify
from reporunner.models import CommandResult, ProjectProfile, SuccessCheck


def result(exit_code=0, stdout="", stderr="", timed_out=False) -> CommandResult:
    return CommandResult(command="python main.py watch", exit_code=exit_code, stdout=stdout, stderr=stderr,
                         timed_out=timed_out, duration_sec=1.0)


def profile(uses_gui=False) -> ProjectProfile:
    return ProjectProfile(python_version="3.12", deps_file=None, has_tests=False, entrypoint="main.py", uses_gui=uses_gui)


# ---------- classify_smoke ----------

def test_still_running_at_timeout_is_alive():
    assert smoke.classify_smoke(result(exit_code=124, timed_out=True)) == "alive"


def test_clean_exit_is_ok():
    assert smoke.classify_smoke(result()) == "ok"


def test_usage_error_means_arguments_are_needed():
    assert smoke.classify_smoke(result(exit_code=2, stderr="usage: main.py [-h] {train,watch}")) == "needs_args"


def test_missing_tk_library_is_broken():
    error = "ImportError: libtk8.6.so: cannot open shared object file"
    assert smoke.classify_smoke(result(exit_code=1, stderr=error)) == "broken"


def test_no_display_is_broken():
    assert smoke.classify_smoke(result(exit_code=1, stderr="_tkinter.TclError: no display name and no $DISPLAY")) == "broken"


def test_missing_saved_model_is_not_an_environment_problem():
    assert smoke.classify_smoke(result(exit_code=1, stderr="No saved brain at brain.json. Run train first.")) == "needs_input"


# ---------- פקודות לבדיקה ----------

def test_commands_are_built_from_subcommands():
    assert smoke.smoke_commands("python main.py --help", ["train", "watch"]) == ["python main.py train", "python main.py watch"]


def test_without_subcommands_the_project_itself_runs():
    assert smoke.smoke_commands("python app.py", []) == ["python app.py"]


# ---------- ניתוב ----------

def state(**fields):
    return {"profile": profile(), "success_check": SuccessCheck(command="python main.py"), **fields}


def test_verified_project_without_cli_or_window_goes_straight_to_report():
    assert route_after_verify(state(status="succeeded")) == "report"


def test_verified_cli_goes_to_smoke_test():
    check = SuccessCheck(command="python main.py --help", help_only=True)
    assert route_after_verify(state(status="succeeded", success_check=check)) == "smoke_test"


def test_verified_window_project_goes_to_smoke_test():
    assert route_after_verify(state(status="succeeded", profile=profile(uses_gui=True))) == "smoke_test"


def test_preview_requested_goes_to_open_preview_after_smoke():
    assert route_after_smoke(state(status="succeeded", preview_mode="live")) == "open_preview"


def test_no_preview_requested_goes_to_report_after_smoke():
    assert route_after_smoke(state(status="succeeded", preview_mode="none")) == "report"


def test_broken_smoke_goes_to_diagnosis():
    assert route_after_smoke(state(status="running", attempts=0)) == "diagnose_error"


def test_needs_smoke_and_wants_preview_helpers():
    assert not nodes_preview.needs_smoke(state())
    assert nodes_preview.wants_preview({"preview_mode": "recording"})
    assert not nodes_preview.wants_preview({})


# ---------- תצוגה ----------

def test_desktop_url_points_to_novnc():
    assert display.desktop_url(49152).startswith("http://localhost:49152/vnc.html?autoconnect=1")


def test_recording_path_is_inside_the_run_folder_and_sanitized():
    path = display.recording_path("reporunner-ab12/../x")
    assert path.name == "recording.mp4"
    assert path.parent.name == "reporunner-ab12x"



TREE_WITH_WINDOW = (
    'xwininfo: Window id: 0x1b (the root window) (has no name)\n'
    '  Root window id: 0x1b (the root window) (has no name)\n'
    '  Parent window id: 0x0 (none)\n'
    '     2 children:\n'
    '     0x400001 "Snake": ("tk" "Tk")  1024x768+0+0  +0+0\n'
    '        1 child:\n'
    '        0x400002 (has no name): ()  1x1+-1+-1  +-1+-1\n'
)


def test_count_windows_counts_child_windows_but_not_the_root():
    assert display.count_windows(TREE_WITH_WINDOW) == 2


def test_count_windows_is_zero_for_an_empty_screen():
    assert display.count_windows("  Root window id: 0x1b (the root window)\n     0 children.\n") == 0
