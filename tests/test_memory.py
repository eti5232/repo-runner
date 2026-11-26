"""בדיקות לזיכרון של v2: היסטוריית ניסיונות וחסימת תיקון שכבר נכשל. לא דורשות Docker או מודל אמיתי."""
from types import SimpleNamespace

from reporunner import memory, nodes
from reporunner.context import RunContext
from reporunner.models import Attempt, CommandResult, Diagnosis, Fix, ProjectProfile

V1, V2 = SimpleNamespace(context=RunContext("v1")), SimpleNamespace(context=RunContext("v2"))


def attempt(number=1, commands=("pip install foo",)) -> Attempt:
    return Attempt(number=number, failed_command="python main.py", error="ModuleNotFoundError: foo",
                   category="missing_package", fix_commands=list(commands))


def state(history) -> dict:
    result = CommandResult(command="python main.py", exit_code=1, stdout="", stderr="boom", timed_out=False, duration_sec=0.1)
    return {
        "last_result": result,
        "profile": ProjectProfile(python_version="3.12", deps_file=None, has_tests=False, entrypoint="main.py"),
        "diagnosis": Diagnosis(category="missing_package", summary="s", root_cause="r"),
        "attempts": len(history),
        "attempt_history": history,
    }


def test_same_commands_with_different_spacing_are_a_repeat():
    assert memory.is_repeat(["pip   install  foo "], [attempt()])
    assert not memory.is_repeat(["pip install foo==2"], [attempt()])
    assert not memory.is_repeat([], [attempt(commands=())])


def test_history_text_is_empty_without_attempts_and_marks_errors_as_data():
    assert memory.history_text([]) == ""
    text = memory.history_text([attempt()])
    assert "pip install foo" in text and "<error_output>" in text


class FakeModel:
    """מחזיר תיקונים לפי הסדר, ורושם מה נשלח אליו."""

    answers: list = []
    calls: list = []

    def __init__(self, *args, **kwargs):
        pass

    def with_structured_output(self, schema):
        return self

    def invoke(self, messages):
        FakeModel.calls.append([m.content for m in messages])
        commands = FakeModel.answers[min(len(FakeModel.calls), len(FakeModel.answers)) - 1]
        return Fix(commands=commands, explanation="x")


def propose(monkeypatch, answers, history, runtime):
    monkeypatch.setattr(nodes, "ChatOpenAI", FakeModel)
    FakeModel.answers, FakeModel.calls = answers, []
    return nodes.propose_fix(state(history), runtime)


def test_v2_blocks_a_repeated_fix_and_asks_again(monkeypatch):
    update = propose(monkeypatch, [["pip install foo"], ["pip install bar"]], [attempt()], V2)
    assert update["proposed_fix"].commands == ["pip install bar"]
    assert len(FakeModel.calls) == 2
    assert "BLOCKED" in FakeModel.calls[1][-1]


def test_v2_sends_the_history_to_the_model(monkeypatch):
    propose(monkeypatch, [["pip install bar"]], [attempt()], V2)
    assert "Previous fix attempts" in FakeModel.calls[0][1]


def test_v1_is_unchanged_no_history_and_no_blocking(monkeypatch):
    update = propose(monkeypatch, [["pip install foo"]], [attempt()], V1)
    assert update["proposed_fix"].commands == ["pip install foo"]
    assert len(FakeModel.calls) == 1
    assert "Previous fix attempts" not in FakeModel.calls[0][1]


def gate(runtime, commands, history):
    fix = Fix(commands=commands, explanation="x")
    return nodes.safety_gate({"proposed_fix": fix, "attempt_history": history}, runtime)["fix_risks"]


def test_a_fix_that_still_repeats_goes_to_a_human_only_in_v2():
    history = [attempt(1), attempt(2)]  # השני הוא ההצעה הנוכחית, והוא זהה לראשון
    assert [risk.kind for risk in gate(V2, ["pip install foo"], history)] == ["repeated"]
    assert gate(V1, ["pip install foo"], history) == []


def test_a_first_time_fix_is_not_marked_as_repeated():
    assert gate(V2, ["pip install foo"], [attempt(1)]) == []
