"""בדיקות לפונקציות הניתוב של הגרף. הן פונקציות רגילות על dict, ולכן לא צריך Docker או מודל.

הרצה:  python -m pytest tests/test_routing.py -v
"""
import pytest

from reporunner import config
from reporunner.graph import (
    route_after_approval, route_after_diagnose, route_after_execute, route_after_safety, route_after_verify,
)
from reporunner.models import CommandResult, Diagnosis, ProjectProfile, Risk, Step


def _result(exit_code: int) -> CommandResult:
    return CommandResult(command="x", exit_code=exit_code, stdout="", stderr="", timed_out=False, duration_sec=0.1)


def _state(exit_code: int, step_index: int, plan_size: int = 3, **extra) -> dict:
    plan = [Step(command=f"cmd{i}", purpose="") for i in range(plan_size)]
    return {"last_result": _result(exit_code), "step_index": step_index, "plan": plan, **extra}


# --- אחרי הרצת צעד ---

def test_success_with_more_steps_loops_back():
    assert route_after_execute(_state(0, step_index=1)) == "execute_step"


def test_success_on_last_step_goes_to_verify():
    assert route_after_execute(_state(0, step_index=3)) == "verify"


def test_failure_goes_to_diagnosis():
    assert route_after_execute(_state(1, step_index=1)) == "diagnose_error"


# --- אחרי אימות ---

def test_verify_success_goes_to_report():
    assert route_after_verify(_state(0, step_index=3, status="succeeded")) == "report"


def test_verify_failure_goes_to_diagnosis():
    assert route_after_verify(_state(1, step_index=3, status="running")) == "diagnose_error"


def test_verify_failure_after_max_attempts_asks_human():
    assert route_after_verify(_state(1, step_index=3, status="running", attempts=config.MAX_ATTEMPTS)) == "human_approval"


# --- אחרי שער הבטיחות ואישור אדם ---

def test_safe_fix_is_applied_without_asking():
    assert route_after_safety({"fix_risks": []}) == "apply_fix"


def test_risky_fix_waits_for_human():
    assert route_after_safety({"fix_risks": [Risk(kind="system", command="apt-get install x")]}) == "human_approval"


def test_attempts_exhausted_asks_human():
    assert route_after_execute(_state(1, step_index=1, attempts=config.MAX_ATTEMPTS)) == "human_approval"


def test_human_can_grant_more_attempts():
    state = _state(1, step_index=1, attempts=config.MAX_ATTEMPTS, attempt_limit=config.MAX_ATTEMPTS + 4)
    assert route_after_execute(state) == "diagnose_error"


@pytest.mark.parametrize("decision, expected", [
    ("approve", "apply_fix"),
    ("reject", "propose_fix"),
    ("continue", "diagnose_error"),
    ("stop", "report"),
])
def test_human_decision_routing(decision, expected):
    assert route_after_approval(_state(1, step_index=1, decision=decision)) == expected


def test_secret_provided_resumes_at_failed_step():
    assert route_after_approval(_state(1, step_index=1, decision="provided")) == "execute_step"


def test_secret_provided_after_verify_failure_resumes_at_verify():
    """כש-verify נכשל, כל הצעדים כבר עברו (step_index == len(plan)); לחזור ל-execute_step היה קורס."""
    assert route_after_approval(_state(1, step_index=3, decision="provided")) == "verify"


def test_missing_env_var_goes_to_human_not_to_fix():
    diagnosis = Diagnosis(category="missing_env_var", summary="s", root_cause="r", env_var_name="API_KEY")
    assert route_after_diagnose({"diagnosis": diagnosis}) == "human_approval"


# --- אחרי אבחון ---

def test_diagnosis_ready_goes_to_fix():
    diagnosis = Diagnosis(category="missing_package", summary="s", root_cause="r")
    assert route_after_diagnose({"diagnosis": diagnosis}) == "propose_fix"


@pytest.mark.parametrize("version, expected", [
    ("3.11", "switch_python"),   # גרסה מוכרת ושונה מהנוכחית
    ("3.12", "propose_fix"),     # זו הגרסה הנוכחית – אין מה להחליף
    ("2.7", "propose_fix"),      # גרסה שלא נתמכת
    (None, "propose_fix"),       # המודל לא ציין גרסה
])
def test_python_version_diagnosis_switches_only_to_a_supported_new_version(version, expected):
    profile = ProjectProfile(python_version="3.12", deps_file=None, has_tests=False, entrypoint=None)
    diagnosis = Diagnosis(category="python_version", summary="s", root_cause="r", python_version=version)
    assert route_after_diagnose({"diagnosis": diagnosis, "profile": profile}) == expected


def test_no_diagnosis_yet_goes_to_investigate():
    assert route_after_diagnose({"diagnosis": None}) == "investigate"
