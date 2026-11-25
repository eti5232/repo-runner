"""בדיקות לבניית ה-Dockerfile והדוח. פונקציות טהורות: בלי Docker ובלי מודל.

הרצה:  python -m pytest tests/test_artifacts.py -v
"""
from reporunner.artifacts import (
    build_dockerfile, build_fixes, build_report, build_run_script, parse_cli_help, run_command,
)
from reporunner.models import Approval, Attempt, CommandResult, ProjectProfile, Step, SuccessCheck

PROFILE = ProjectProfile(python_version="3.11", deps_file="requirements.txt", has_tests=False, entrypoint="main.py")


def _result(stdout: str = "", exit_code: int = 0) -> CommandResult:
    return CommandResult(command="python main.py", exit_code=exit_code, stdout=stdout, stderr="", timed_out=False, duration_sec=1)


def _state(**extra) -> dict:
    plan = [Step(command="python --version", purpose="", in_dockerfile=False),
            Step(command="pip install -r requirements.txt", purpose="")]
    return {"profile": PROFILE, "plan": plan, "step_index": 2, "status": "succeeded", "last_result": _result(),
            "success_check": SuccessCheck(command="python main.py", kind="run"), **extra}


def test_dockerfile_starts_with_syntax_line_and_uses_detected_python():
    text = build_dockerfile(PROFILE, ["pip install -r requirements.txt"], "python main.py", [], None, True)
    lines = text.splitlines()
    assert lines[0] == "# syntax=docker/dockerfile:1"
    assert "FROM python:3.11-slim" in lines
    assert "RUN pip install -r requirements.txt" in lines
    assert lines[-1] == 'CMD ["sh", "-c", "python main.py"]'


def test_dockerfile_exposes_port_and_mentions_required_env_vars_without_values():
    text = build_dockerfile(PROFILE, [], "python main.py", ["SERVICE_API_KEY"], 8080, True)
    assert "EXPOSE 8080" in text
    assert "docker run -e SERVICE_API_KEY=<value>" in text


def test_failed_run_is_marked_in_the_dockerfile():
    assert "WARNING" in build_dockerfile(PROFILE, [], "python main.py", [], None, False)


def test_heredoc_step_is_kept_as_is():
    step = "python - <<'PY'\nprint('x')\nPY"
    assert f"RUN {step}" in build_dockerfile(PROFILE, [step], "python main.py", [], None, True)


def test_multiline_step_without_heredoc_is_joined():
    text = build_dockerfile(PROFILE, ["pip install a\npip install b"], "python main.py", [], None, True)
    assert "RUN pip install a && \\\n    pip install b" in text


def test_cli_dockerfile_uses_entrypoint_so_a_subcommand_can_be_appended():
    text = build_dockerfile(PROFILE, [], "python main.py", [], None, True, help_only=True)
    assert text.splitlines()[-2:] == ['ENTRYPOINT ["python", "main.py"]', 'CMD ["--help"]']


ARGPARSE_HELP = """usage: main.py [-h] {train,watch,learn} ...

positional arguments:
  {train,watch,learn}
    train               Train the agent from scratch
    watch               Watch the trained agent play
    learn

options:
  -h, --help            show this help message and exit
"""


def test_parse_cli_help_extracts_descriptions_and_tolerates_missing_ones():
    assert parse_cli_help(ARGPARSE_HELP) == {
        "train": "Train the agent from scratch", "watch": "Watch the trained agent play", "learn": ""}


def test_parse_cli_help_joins_a_description_that_argparse_wrapped():
    wrapped = ("usage: main.py [-h] {train,learn} ...\n\npositional arguments:\n  {train,learn}\n"
               "    train               train without a window\n"
               "    learn               watch the brain learn live (saved when you close the\n"
               "                        window)\n\noptions:\n  -h, --help            show this help\n")
    assert parse_cli_help(wrapped)["learn"] == "watch the brain learn live (saved when you close the window)"
    assert parse_cli_help(wrapped)["train"] == "train without a window"


def test_parse_cli_help_without_subcommands_is_empty():
    assert parse_cli_help("usage: main.py [-h] [--name NAME]") == {}


def test_cli_report_carries_the_command_to_run_and_the_descriptions():
    check = SuccessCheck(command="python main.py --help", help_only=True, timeout=30)
    report = build_report(_state(success_check=check, last_result=_result(ARGPARSE_HELP)))
    assert report.run_command == "python main.py"
    assert report.cli_help["watch"] == "Watch the trained agent play"


def test_cli_report_lists_subcommands_and_says_nothing_real_was_run():
    help_text = "usage: main.py [-h] {train,watch,learn} ..."
    check = SuccessCheck(command="python main.py --help", help_only=True, timeout=30)
    report = build_report(_state(success_check=check, last_result=_result(help_text)))
    assert report.help_only and report.cli_commands == ["train", "watch", "learn"]
    assert "--help" in report.summary and "לא הורצה פקודה ממשית" in report.summary
    assert report.run_script.splitlines()[-1] == "python main.py --help"


def test_run_script_recreates_the_environment():
    script = build_run_script(["pip install -r requirements.txt"], "python main.py")
    assert script.splitlines()[:4] == ["#!/bin/sh", "set -e", "python -m venv .venv", ". .venv/bin/activate"]
    assert script.splitlines()[-1] == "python main.py"


def test_run_command_prefers_entrypoint_then_tests():
    check = SuccessCheck(command="python -m pytest --collect-only -q")
    assert run_command(PROFILE, check) == "python main.py"
    no_entry = ProjectProfile(python_version="3.12", deps_file=None, has_tests=True, entrypoint=None)
    assert run_command(no_entry, check) == "python -m pytest -q"


def test_report_learns_port_from_server_check_and_lists_secrets():
    state = _state(last_result=_result("hi\nSERVER_OK port 8080"),
                   approvals=[Approval(kind="secret_needed", action="provided", detail="API_KEY")])
    report = build_report(state)
    assert report.succeeded and report.port == 8080 and report.env_vars == ["API_KEY"]
    assert "python:3.11" in report.dockerfile


def test_failed_report_summarizes_the_failing_command():
    report = build_report(_state(status="running", last_result=_result(exit_code=1), attempts=3))
    assert not report.succeeded
    assert "python main.py" in report.summary and "3" in report.summary


def test_provided_secret_is_listed_as_a_fix_without_its_value():
    fixes = build_fixes({"approvals": [Approval(kind="secret_needed", action="provided", detail="API_KEY")]})
    assert fixes == ["1. [missing_env_var] סופק המשתנה API_KEY (הערך אינו נשמר)"]


def test_fixes_list_shows_what_broke_and_how_it_was_fixed():
    attempt = Attempt(number=1, failed_command="python main.py", error="e", category="missing_package",
                      fix_commands=["pip install PyYAML"])
    assert build_fixes({"attempt_history": [attempt]}) == ["1. [missing_package] נכשל: python main.py | תיקון: pip install PyYAML"]
