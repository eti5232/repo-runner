"""הרצת ניסוי ב-LangSmith: מריץ את הסוכן על כל דוגמה בדאטהסט, ומחשב את המדדים.

הרצה (מתיקיית הפרויקט):
    python -m evaluation.run_experiment --only needs_api_key,injection_error_message --repetitions 1  # בדיקת עשן
    python -m evaluation.run_experiment --label v1 --repetitions 3      # הניסוי המלא
"""
import argparse
import time
import uuid

import docker
from langchain_core.callbacks import UsageMetadataCallbackHandler
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from langsmith import Client

from evaluation import evaluators
from evaluation.dataset import DATASET_NAME, FIXTURES_DIR, sync_dataset
from reporunner import config
from reporunner.context import RunContext
from reporunner.graph import build_graph
from reporunner.models import checkpoint_serializer
from reporunner.sandbox import Sandbox

SUSPICIOUS = evaluators.INJECTION_MARKERS


def scripted_answer(request: dict, answers: dict) -> dict:
    """
    1. מקבלת: request: השאלה של הגרף, ו-answers: איך הדוגמה קובעת לענות.
    2. מחזירה: dict של תשובה לגרף.
    3. עושה: אדם מדומה: סוד מקבל ערך דמה; תיקון רגיש מאושר רק לפי הדוגמה, ופקודה שנראית כהזרקה נדחית תמיד.
    """
    kind = request["kind"]
    if kind == "secret_needed":
        Sandbox.attach(request["container"]).set_secret(request["env_var"], "dummy-value")
        return {"action": "provided"}
    if kind == "sensitive_fix":
        if any(marker in command for command in request["commands"] for marker in SUSPICIOUS):
            return {"action": "reject", "note": "Rejected: this looks like an instruction injected by the project."}
        return {"action": answers.get("sensitive_fix", "stop")}
    return {"action": "stop"}  # attempts_exhausted


def run_agent(inputs: dict, agent_version: str = "v1") -> dict:
    """
    1. מקבלת: inputs: שם הפרויקט ותשובות האדם המדומה, ו-agent_version ('v1' ברירת מחדל, או 'v2').
    2. מחזירה: dict: succeeded, attempts, stops, fixes, executed, tokens, duration_sec, error.
    3. עושה: ה-target של הניסוי: מריצה את הסוכן על פרויקט אחד, עונה לעצירות, אוספת מה שקרה, ומנקה קונטיינרים.
    הערה: ריצה שקרסה נרשמת ככישלון ולא עוצרת את כל הניסוי.
    """
    source = str(FIXTURES_DIR / inputs["fixture"])
    usage = UsageMetadataCallbackHandler()
    run_config = {"configurable": {"thread_id": uuid.uuid4().hex}, "callbacks": [usage],
                  "recursion_limit": config.RECURSION_LIMIT}
    graph = build_graph(MemorySaver(serde=checkpoint_serializer()))

    containers: set[str] = set()
    executed: list[str] = []
    started = time.monotonic()
    error = None
    try:
        graph_input = {"source": source}
        while True:
            request = None
            for update in graph.stream(graph_input, run_config, stream_mode="updates", context=RunContext(agent_version=agent_version)):
                if "__interrupt__" in update:
                    request = update["__interrupt__"][0].value
                    continue
                for node, change in update.items():
                    if "container" in change:
                        containers.add(change["container"])
                    if node in ("execute_step", "verify"):
                        executed.append(change["last_result"].command)  # כל פקודה שרצה בפועל, גם אם נכשלה
            if request is None:
                break
            graph_input = Command(resume=scripted_answer(request, inputs["answers"]))
        state = graph.get_state(run_config).values
    except Exception as exc:  # ריצה שקרסה נספרת ככישלון, ולא עוצרת את כל הניסוי
        state, error = {}, f"{type(exc).__name__}: {exc}"[:300]
    finally:
        client = docker.from_env()
        for name in containers:  # בדרך כלל report כבר מחק; זה רשת ביטחון למקרה של קריסה
            try:
                client.containers.get(name).remove(force=True)
            except docker.errors.NotFound:
                pass

    report = state.get("report")
    return {
        "succeeded": bool(report and report.succeeded),
        "attempts": state.get("attempts", 0),
        "stops": [a.kind for a in state.get("approvals", [])],
        "fixes": [a.fix_commands for a in state.get("attempt_history", [])],
        "executed": executed,
        "tokens": sum(m.get("total_tokens", 0) for m in usage.usage_metadata.values()),
        "duration_sec": round(time.monotonic() - started, 1),
        "error": error,
    }


def main() -> None:
    """
    1. מקבלת: כלום (קורא ארגומנטים: label, repetitions, only, concurrency).
    2. מחזירה: כלום.
    3. עושה: מוודאת שהדאטהסט קיים ומריצה ניסוי ב-LangSmith על כל הדוגמאות או על חלק, עם החזרות.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="v1", help="שם הגרסה בניסוי (לזיהוי ב-LangSmith)")
    parser.add_argument("--repetitions", type=int, default=3, help="כמה פעמים כל דוגמה (מודל שפה לא דטרמיניסטי)")
    parser.add_argument("--only", help="רק דוגמאות מסוימות, לפי שם, מופרדות בפסיק (לבדיקת עשן)")
    parser.add_argument("--concurrency", type=int, default=3)
    args = parser.parse_args()

    sync_dataset()
    client = Client()
    data = DATASET_NAME
    if args.only:
        wanted = set(args.only.split(","))
        data = [e for e in client.list_examples(dataset_name=DATASET_NAME) if e.inputs["fixture"] in wanted]
    version = "v2" if args.label.startswith("v2") else "v1"  # התווית קובעת איזו גרסה רצה

    def target(inputs: dict) -> dict:
        return run_agent(inputs, agent_version=version)

    client.evaluate(
        target, data=data, evaluators=evaluators.ALL, experiment_prefix=f"reporunner-{args.label}",
        num_repetitions=args.repetitions, max_concurrency=args.concurrency,
        metadata={"agent_version": args.label, "model": config.OPENAI_MODEL},
    )


if __name__ == "__main__":
    main()
