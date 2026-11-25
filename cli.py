"""הרצת הסוכן מהטרמינל.

דוגמאות:
    python cli.py evaluation/fixtures/broken_missing_dep
    python cli.py https://github.com/user/repo --commit abc123
    python cli.py --resume --thread 1a2b3c4d        # המשך ריצה שנעצרה לאישור
"""
import argparse
import getpass
import sqlite3
import sys
import uuid

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from reporunner import artifacts, config
from reporunner.graph import build_graph
from reporunner.models import checkpoint_serializer
from reporunner.sandbox import Sandbox

RISK_LABELS = {
    "system": "התקנה מערכתית / הרשאות root",
    "remote_script": "הרצת סקריפט שהורד מהרשת",
    "secret": "הגדרת סוד",
    "code_change": "שינוי בקוד המקור",
    "custom_source": "התקנה ממקור מותאם",
    "outside": "פעולה מחוץ לתיקיית הפרויקט",
    "unrecognized": "פקודה שלא זוהתה",
}


def describe(node: str, change: dict) -> str:
    """
    1. מקבלת: node (שם הצומת) ו-change (מה ששינה ב-State).
    2. מחזירה: שורת תיאור קצרה בעברית.
    3. עושה: מתרגמת עדכון של צומת לשורת התקדמות קריאה. משמשת גם את הממשק הגרפי.
    """
    if node == "clone_repo":
        return f"קונטיינר מוכן: {change['container']}"
    if node == "analyze_project":
        p = change["profile"]
        return f"תלויות: {p.deps_file or 'אין'} | בדיקות: {'כן' if p.has_tests else 'לא'} | כניסה: {p.entrypoint or 'אין'}"
    if node == "plan_run":
        return f"{len(change['plan'])} צעדים, בדיקת הצלחה: {change['success_check'].command}"
    if node in ("execute_step", "verify"):
        r = change["last_result"]
        mark = "✔" if r.ok else "✘"
        return f"{mark} {r.command}  ({r.duration_sec} שנ')" + ("" if r.ok else f"\n{r.stderr or r.stdout}")
    if node == "diagnose_error":
        if change.get("diagnosis"):
            d = change["diagnosis"]
            return f"אבחון [{d.category}]: {d.summary}"
        calls = change["messages"][-1].tool_calls
        return "חוקר: " + ", ".join(f"{c['name']}({', '.join(map(str, c['args'].values()))})" for c in calls)
    if node == "investigate":
        return f"{len(change['messages'])} תוצאות כלים"
    if node == "propose_fix":
        return "תיקון מוצע: " + " && ".join(change["proposed_fix"].commands)
    if node == "switch_python":
        return f"עבר ל-Python {change['profile'].python_version} (קונטיינר חדש: {change['container']})"
    if node == "safety_gate":
        return "דורש אישור" if change["fix_risks"] else "בטוח – רץ אוטומטית"
    if node == "human_approval":
        return f"החלטה: {change['decision']}"
    return ""


def _read_secret(prompt: str) -> str:
    """
    1. מקבלת: prompt: הטקסט להצגה.
    2. מחזירה: מחרוזת שהוקלדה.
    3. עושה: בטרמינל אמיתי קוראת בלי הד למסך (getpass); כשהקלט מצינור, input רגיל (לבדיקות).
    """
    return getpass.getpass(prompt) if sys.stdin.isatty() else input(prompt)


def ask_human(request: dict) -> dict:
    """
    1. מקבלת: request: השאלה שעצרה את הגרף.
    2. מחזירה: dict עם התשובה, בפורמט ש-human_approval מצפה לו.
    3. עושה: מציגה את בקשת האישור ושואלת את המשתמש. בסוד, כותבת אותו ישירות לקונטיינר ולא לגרף.
    """
    kind = request["kind"]
    print("\n⏸  הסוכן עצר וממתין להחלטה שלך")

    if kind == "secret_needed":
        name = request["env_var"]
        print(f"   הפרויקט דורש את המשתנה {name}: {request['summary']}")
        value = _read_secret(f"   ערך ל-{name} (Enter = ערך דמה): ")
        # הסוד נכתב ישירות לקונטיינר. הוא לא נכנס ל-State, ל-checkpointer או ל-LangSmith
        Sandbox.attach(request["container"]).set_secret(name, value or "dummy-value")
        return {"action": "provided"}

    if kind == "sensitive_fix":
        print(f"   תיקון מוצע: {request['explanation']}")
        for risk in request["risks"]:
            print(f"   ⚠ {RISK_LABELS[risk['kind']]}: {risk['command']}")
        answer = input("   [y] אשר   [n] דחה   [s] עצור   : ").strip().lower()
        if answer == "y":
            return {"action": "approve"}
        if answer == "n":
            return {"action": "reject", "note": input("   סיבה לדחייה (לא חובה): ").strip()}
        return {"action": "stop"}

    print(f"   נוסו {request['attempts']} תיקונים ועדיין לא עובד.")
    answer = input(f"   [c] המשך ({config.ATTEMPTS_GRANT} ניסיונות נוספים)   [s] עצור   : ").strip().lower()
    return {"action": "continue" if answer == "c" else "stop"}


def save_report(report, thread: str, source: str):
    """
    1. מקבלת: report, thread (מזהה ריצה), source.
    2. מחזירה: נתיב התיקייה שנוצרה.
    3. עושה: שומרת Dockerfile, run.sh ו-REPORT.md בתיקיית הריצה, עם סוף שורה של לינוקס.
    """
    folder = config.RUNS_DIR / thread
    folder.mkdir(parents=True, exist_ok=True)
    # newline="\n": Dockerfile וסקריפט shell חייבים סוף שורה של לינוקס, גם כשכותבים מ-Windows
    (folder / "Dockerfile").write_text(report.dockerfile, encoding="utf-8", newline="\n")
    (folder / "run.sh").write_text(report.run_script, encoding="utf-8", newline="\n")
    (folder / "REPORT.md").write_text(artifacts.render_markdown(report, source), encoding="utf-8")
    return folder


def pending_request(graph, run_config) -> dict | None:
    """
    1. מקבלת: graph ו-run_config.
    2. מחזירה: dict של השאלה הממתינה, או None.
    3. עושה: בודקת אם הריצה נעצרה בהמתנה לאדם, ומחזירה את השאלה.
    """
    interrupts = graph.get_state(run_config).interrupts
    return interrupts[0].value if interrupts else None


def main() -> None:
    """
    1. מקבלת: כלום (קורא ארגומנטים משורת הפקודה).
    2. מחזירה: כלום.
    3. עושה: מריצה את הגרף עם שמירת מצב, מדפיסה התקדמות, שואלת בכל עצירה, ובסוף שומרת תוצרים. עם --resume ממשיכה ריצה שנעצרה.
    """
    sys.stdout.reconfigure(encoding="utf-8")  # כדי שעברית תוצג נכון בטרמינל של Windows (רק בהרצה מהטרמינל)
    parser = argparse.ArgumentParser(description="RepoRunner – מריץ פרויקט Python בקונטיינר")
    parser.add_argument("source", nargs="?", help="קישור GitHub או נתיב לתיקייה מקומית")
    parser.add_argument("--commit", help="commit מסוים (לפרויקט מ-GitHub)")
    parser.add_argument("--thread", default=uuid.uuid4().hex[:8], help="מזהה הריצה (לשמירה והמשך)")
    parser.add_argument("--resume", action="store_true", help="המשך ריצה שנעצרה לאישור")
    args = parser.parse_args()
    if not args.resume and not args.source:
        parser.error("חובה לציין פרויקט, או --resume --thread ID")

    config.CHECKPOINT_DB.parent.mkdir(exist_ok=True)
    run_config = {"configurable": {"thread_id": args.thread}, "recursion_limit": config.RECURSION_LIMIT}
    final_report = None

    # SqliteSaver שומר את ה-State בקובץ אחרי כל צומת – לכן אפשר לסגור את התוכנה ולהמשיך
    connection = sqlite3.connect(str(config.CHECKPOINT_DB), check_same_thread=False)
    try:
        graph = build_graph(SqliteSaver(connection, serde=checkpoint_serializer()))

        if args.resume:
            request = pending_request(graph, run_config)
            if request is None:
                sys.exit(f"אין ריצה ממתינה עם המזהה {args.thread}")
            inputs = Command(resume=ask_human(request))
        else:
            print(f"מזהה ריצה: {args.thread}")
            inputs = {"source": args.source, "commit": args.commit}

        try:
            while True:
                request = None
                # stream_mode="updates": אחרי כל צומת מקבלים רק את השדות שהוא שינה
                for update in graph.stream(inputs, run_config, stream_mode="updates"):
                    if "__interrupt__" in update:
                        request = update["__interrupt__"][0].value
                        continue
                    for node, change in update.items():
                        print(f"[{node}] {describe(node, change)}")
                        final_report = change.get("report", final_report)
                if request is None:
                    break
                inputs = Command(resume=ask_human(request))
        except EOFError:
            # אין מי שיענה (למשל הקלט נסגר). המצב כבר נשמר ב-checkpointer
            print(f"\nהריצה נעצרה וממתינה לתשובה. להמשך:\n  python cli.py --resume --thread {args.thread}")
            return
    finally:
        connection.close()

    folder = save_report(final_report, args.thread, args.source or "")
    print("\n" + final_report.summary)
    print(f"\nהתוצרים נשמרו ב: {folder}\n  Dockerfile, run.sh, REPORT.md")


if __name__ == "__main__":
    main()
