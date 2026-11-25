"""בניית הגרף: אילו צמתים יש, ואיך עוברים ביניהם."""
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import RetryPolicy

from reporunner import config, nodes, nodes_preview
from reporunner.context import RunContext
from reporunner.state import RunState
from reporunner.tools import INVESTIGATION_TOOLS


def _fix_or_give_up(state: RunState) -> str:
    """
    1. מקבלת: state.
    2. מחזירה: 'diagnose_error' או 'human_approval'.
    3. עושה: אם נותרו ניסיונות (attempts קטן מהמגבלה) שולחת לאבחון; אחרת שואלת אדם אם להמשיך.
    """
    limit = state.get("attempt_limit", config.MAX_ATTEMPTS)
    return "diagnose_error" if state.get("attempts", 0) < limit else "human_approval"


def route_after_execute(state: RunState) -> str:
    """
    1. מקבלת: state.
    2. מחזירה: שם הצומת הבא: execute_step, verify, diagnose_error או human_approval.
    3. עושה: צעד הצליח ויש עוד: חוזרת לאותו צומת (לולאת הצעדים); הצליח והאחרון: אימות; נכשל: אבחון או שאלה לאדם.
    """
    if state["last_result"].ok:
        if state["step_index"] < len(state["plan"]):
            return "execute_step"  # לולאת הצעדים: חוזרים לאותו צומת עם הצעד הבא
        return "verify"
    return _fix_or_give_up(state)


def _after_success(state: RunState) -> str:
    """
    1. מקבלת: state (הפרויקט עבר אימות או בדיקת פקודות).
    2. מחזירה: 'open_preview' או 'report'.
    3. עושה: אם המשתמשת ביקשה תצוגה חיה או הקלטה עוברת להכנתה, אחרת ישר לדוח.
    """
    return "open_preview" if nodes_preview.wants_preview(state) else "report"


def route_after_verify(state: RunState) -> str:
    """
    1. מקבלת: state.
    2. מחזירה: 'smoke_test', 'open_preview', 'report', 'diagnose_error' או 'human_approval'.
    3. עושה: אימות הצליח: בדיקת פקודות אם יש פקודות משנה או חלון, אחרת תצוגה או דוח. אימות נכשל: טיפול בכשל.
    """
    if state.get("status") == "succeeded":
        return "smoke_test" if nodes_preview.needs_smoke(state) else _after_success(state)
    return _fix_or_give_up(state)


def route_after_smoke(state: RunState) -> str:
    """
    1. מקבלת: state (אחרי smoke_test).
    2. מחזירה: 'open_preview', 'report', 'diagnose_error' או 'human_approval'.
    3. עושה: הבדיקה עברה (status=succeeded): תצוגה או דוח. פקודה נשברה בגלל הסביבה: טיפול בכשל, כמו אחרי כשל הרצה.
    """
    if state.get("status") == "succeeded":
        return _after_success(state)
    return _fix_or_give_up(state)


def route_after_diagnose(state: RunState) -> str:
    """
    1. מקבלת: state.
    2. מחזירה: 'investigate', 'propose_fix', 'human_approval' או 'switch_python'.
    3. עושה: אין אבחון עדיין: חקירה. חסר סוד: אדם. גרסת Python מוכרת ושונה מהנוכחית: מעבר גרסה. אחרת: הצעת תיקון.
    """
    diagnosis = state.get("diagnosis")
    if not diagnosis:
        return "investigate"
    if diagnosis.category == "missing_env_var" and diagnosis.env_var_name:
        return "human_approval"  # סוד אמיתי אי אפשר להמציא; רק אדם יכול לספק אותו
    if (diagnosis.category == "python_version" and diagnosis.python_version in config.SUPPORTED_PYTHON
            and diagnosis.python_version != state["profile"].python_version):
        return "switch_python"  # גרסה מוכרת ושונה מהנוכחית; אחרת נופלים לתיקון רגיל
    return "propose_fix"


def route_after_safety(state: RunState) -> str:
    """
    1. מקבלת: state.
    2. מחזירה: 'apply_fix' או 'human_approval'.
    3. עושה: תיקון בלי סיכונים מוחל אוטומטית; תיקון עם סיכון עובר לאישור אדם.
    """
    return "human_approval" if state.get("fix_risks") else "apply_fix"


def route_resume(state: RunState) -> str:
    """
    1. מקבלת: state.
    2. מחזירה: 'execute_step' או 'verify'.
    3. עושה: קובעת מאיפה ממשיכים: לצעד הבא בתוכנית, או ל-verify אם כל הצעדים כבר עברו.
    """
    return "execute_step" if state["step_index"] < len(state["plan"]) else "verify"


def route_after_approval(state: RunState) -> str:
    """
    1. מקבלת: state (כולל decision: ההחלטה של האדם).
    2. מחזירה: שם הצומת הבא.
    3. עושה: approve: מחילה תיקון; reject: הצעה חדשה; provided: ממשיכה להריץ; continue: אבחון; כל דבר אחר (stop): דוח.
    """
    return {
        "approve": "apply_fix",
        "reject": "propose_fix",       # מציעים תיקון אחר, עם הסיבה לדחייה
        "provided": route_resume(state),  # הסוד סופק – מריצים שוב את מה שנכשל
        "continue": "diagnose_error",  # קיבלנו עוד ניסיונות
    }.get(state["decision"], "report")  # stop (או כל דבר לא מוכר) – מסיימים


def build_graph(checkpointer=None):
    """
    1. מקבלת: checkpointer (לא חובה): מנגנון שמירת המצב.
    2. מחזירה: גרף LangGraph מקומפל.
    3. עושה: מוסיפה את כל הצמתים והקשתות (כולל הלולאות והענפים המותנים), ומקמפלת. RetryPolicy על צמתי ה-LLM.
    """
    builder = StateGraph(RunState, context_schema=RunContext)

    # שגיאת רשת רגעית מול OpenAI לא אמורה להפיל ריצה שלמה – מנסים שוב אוטומטית
    llm_retry = RetryPolicy(max_attempts=3)

    builder.add_node("clone_repo", nodes.clone_repo)
    builder.add_node("analyze_project", nodes.analyze_project)
    builder.add_node("plan_run", nodes.plan_run)
    builder.add_node("execute_step", nodes.execute_step)
    builder.add_node("verify", nodes.verify)
    builder.add_node("diagnose_error", nodes.diagnose_error, retry_policy=llm_retry)
    builder.add_node("investigate", ToolNode(INVESTIGATION_TOOLS))  # מריץ את הכלים שהמודל ביקש
    builder.add_node("propose_fix", nodes.propose_fix, retry_policy=llm_retry)
    builder.add_node("switch_python", nodes.switch_python)
    builder.add_node("safety_gate", nodes.safety_gate)
    builder.add_node("human_approval", nodes.human_approval)
    builder.add_node("apply_fix", nodes.apply_fix)
    builder.add_node("smoke_test", nodes_preview.smoke_test)
    builder.add_node("open_preview", nodes_preview.open_preview)
    builder.add_node("report", nodes.report)

    builder.add_edge(START, "clone_repo")
    builder.add_edge("clone_repo", "analyze_project")
    builder.add_edge("analyze_project", "plan_run")
    builder.add_edge("plan_run", "execute_step")
    builder.add_conditional_edges("execute_step", route_after_execute, ["execute_step", "verify", "diagnose_error", "human_approval"])
    builder.add_conditional_edges("verify", route_after_verify, ["smoke_test", "open_preview", "report", "diagnose_error", "human_approval"])
    builder.add_conditional_edges("smoke_test", route_after_smoke, ["open_preview", "report", "diagnose_error", "human_approval"])
    builder.add_edge("open_preview", "report")
    builder.add_conditional_edges("diagnose_error", route_after_diagnose, ["investigate", "propose_fix", "human_approval", "switch_python"])
    builder.add_edge("switch_python", "execute_step")  # התוכנית רצה מההתחלה בסביבה החדשה
    builder.add_edge("investigate", "diagnose_error")   # לולאת החקירה
    builder.add_edge("propose_fix", "safety_gate")
    builder.add_conditional_edges("safety_gate", route_after_safety, ["apply_fix", "human_approval"])
    builder.add_conditional_edges("human_approval", route_after_approval, ["apply_fix", "propose_fix", "execute_step", "verify", "diagnose_error", "report"])
    builder.add_conditional_edges("apply_fix", route_resume, ["execute_step", "verify"])  # לולאת התיקון
    builder.add_edge("report", END)

    return builder.compile(checkpointer=checkpointer)


# הגרף שמשמש את langgraph.json (Studio). שרת LangGraph מוסיף שמירת מצב בעצמו.
graph = build_graph()
