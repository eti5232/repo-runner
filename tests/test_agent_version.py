"""בדיקות למנגנון גרסת הסוכן (v1 מול v2). לא דורשות Docker או מודל אמיתי."""
from types import SimpleNamespace

from reporunner import nodes, prompts
from reporunner.context import RunContext, version_of
from reporunner.models import CommandResult, Diagnosis, Fix, ProjectProfile


def test_default_version_is_v1_so_old_experiments_do_not_change():
    assert version_of(None) == "v1"
    assert version_of(RunContext()) == "v1"
    assert version_of(RunContext(agent_version="v2")) == "v2"


def test_v1_prompt_is_the_original_and_has_no_heredoc_rule():
    assert prompts.fix_system("v1") == prompts.FIX_SYSTEM
    assert "heredoc" not in prompts.fix_system("v1")


def test_v2_prompt_adds_the_one_line_rules_and_keeps_the_security_notice_last():
    v2 = prompts.fix_system("v2")
    assert "heredoc" in v2 and "sed -i" in v2
    assert v2.startswith(prompts.FIX_SYSTEM.removesuffix(prompts.UNTRUSTED_NOTICE))
    assert v2.rstrip().endswith(prompts.UNTRUSTED_NOTICE.rstrip())


class FakeModel:
    """מחליף את ChatOpenAI: רושם את הפרומפט שנשלח, ומחזיר תיקון קבוע."""

    sent: list = []

    def __init__(self, *args, **kwargs):
        pass

    def with_structured_output(self, schema):
        return self

    def invoke(self, messages):
        FakeModel.sent = messages
        return Fix(commands=["pip install numpy"], explanation="x")


def _state() -> dict:
    result = CommandResult(command="python main.py", exit_code=1, stdout="", stderr="NameError", timed_out=False, duration_sec=0.1)
    return {
        "last_result": result,
        "profile": ProjectProfile(python_version="3.12", deps_file=None, has_tests=False, entrypoint="main.py"),
        "diagnosis": Diagnosis(category="code_bug", summary="s", root_cause="r"),
        "attempts": 0,
    }


def _system_prompt_used(monkeypatch, context) -> str:
    monkeypatch.setattr(nodes, "ChatOpenAI", FakeModel)
    nodes.propose_fix(_state(), SimpleNamespace(context=context))
    return FakeModel.sent[0].content


def test_propose_fix_uses_the_v1_prompt_by_default(monkeypatch):
    assert _system_prompt_used(monkeypatch, None) == prompts.FIX_SYSTEM


def test_propose_fix_uses_the_v2_prompt_when_the_context_says_v2(monkeypatch):
    assert _system_prompt_used(monkeypatch, RunContext(agent_version="v2")) == prompts.FIX_SYSTEM_V2


def test_diagnosis_prompt_v1_is_the_original_and_v2_asks_for_hebrew():
    assert prompts.diagnose_system("v1") == prompts.DIAGNOSE_SYSTEM
    assert "Hebrew" not in prompts.DIAGNOSE_SYSTEM
    assert "Hebrew" in prompts.diagnose_system("v2")


def test_fix_prompt_v2_asks_for_hebrew_explanations_and_keeps_the_notice_last():
    v2 = prompts.fix_system("v2")
    assert "Hebrew" in v2 and "Hebrew" not in prompts.FIX_SYSTEM
    assert v2.rstrip().endswith(prompts.UNTRUSTED_NOTICE.rstrip())
