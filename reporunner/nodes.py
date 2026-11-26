"""הצמתים של הגרף. כל צומת: מקבל את ה-State, מחזיר dict עם השדות שהוא משנה."""
from pathlib import Path

from langchain_core.messages import HumanMessage, RemoveMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.runtime import Runtime
from langgraph.types import interrupt

from reporunner import artifacts, config, display, entrypoint, memory, prompts, safety
from reporunner.context import RunContext, version_of
from reporunner.models import Approval, Attempt, Diagnosis, Fix, ProjectProfile, Risk, Step, SuccessCheck
from reporunner.sandbox import Sandbox
from reporunner.state import RunState
from reporunner.tools import INVESTIGATION_TOOLS

# ---------- איפה משתמשים במודל ולמה ----------
# עיקרון: LLM רק איפה שצריך שיפוט. כל מה שאפשר לקבוע בכללים ברורים נעשה בקוד דטרמיניסטי:
# הוא זול, מיידי, נותן תמיד אותה תשובה (חשוב לניסויים), ולא ניתן לשכנוע ע"י טקסט זדוני.
#
# צמתים שקוראים למודל (מודל אחד, OPENAI_MODEL, בשני תפקידים):
#   diagnose_error – להבין שגיאה: הודעת שגיאה היא טקסט חופשי, והמודל מחליט אילו קבצים לקרוא
#                    (לולאת ReAct) ומסווג את הסיבה. אין כלל קבוע שיודע לפרש כל שגיאה אפשרית.
#   propose_fix    – להציע תיקון קונקרטי לפי האבחון. דורש יצירתיות ("איזו חבילה חסרה? איזו גרסה?").
#
# צמתים בלי מודל (קוד בלבד):
#   clone_repo, analyze_project, plan_run – התאמת שמות קבצים לרשימות קבועות.
#   execute_step, verify                  – הרצת פקודה ובדיקת קוד יציאה או שרת שעונה. "הצלחה" נקבעת
#                                           בהרצה אמיתית, לא לפי דעת המודל.
#   investigate (tools.py)                – כלי קריאה (list_files, read_file, search_text) שהמודל מפעיל.
#   safety_gate                           – כללי בטיחות קבועים. ההחלטה אם פקודה מסוכנת לא נמסרת למודל,
#                                           כדי שמודל ש"שוכנע" לא יוכל לעקוף אותה.
#   human_approval, apply_fix, switch_python, report – ניהול זרימה ובניית תוצרים.

DEPS_FILES = ("requirements.txt", "pyproject.toml", "setup.py")  # לפי סדר עדיפות


def _sandbox(state: RunState) -> Sandbox:
    """
    1. מקבלת: state.
    2. מחזירה: Sandbox מחובר לקונטיינר של הריצה.
    3. עושה: מתחברת מחדש לקונטיינר לפי השם ששמור ב-state['container'].
    """
    return Sandbox.attach(state["container"])


# ---------- 1. הכנת הקונטיינר והפרויקט ----------

def clone_repo(state: RunState) -> dict:
    """
    1. מקבלת: state עם source (נתיב מקומי או קישור GitHub) ו-commit (לא חובה).
    2. מחזירה: {container, status}.
    3. עושה: יוצרת קונטיינר ומכניסה אליו את הפרויקט; אם ההעתקה נכשלת מוחקת את הקונטיינר.
    """
    box = Sandbox()
    box.start()
    try:
        source = state["source"]
        skipped: list[str] = []
        if Path(source).is_dir():
            skipped = box.copy_project(Path(source))
        else:
            box.clone_project(source, state.get("commit"))
    except Exception:
        box.stop()  # כמו ב-start(): אם נכשלנו באמצע, לא משאירים קונטיינר יתום
        raise
    return {"container": box.name, "status": "running", "skipped": skipped}


def analyze_project(state: RunState) -> dict:
    """
    1. מקבלת: state.
    2. מחזירה: {profile}: קובץ תלויות, האם יש בדיקות, נקודת כניסה, והאם הפרויקט פותח חלון.
    3. עושה: סורקת את קבצי הפרויקט לפי כללים קבועים, בלי LLM.
    """
    box = _sandbox(state)
    listing = box.run("find . -maxdepth 2 -type f -not -path './.git/*'")
    files = {line.removeprefix("./") for line in listing.stdout.splitlines()}

    entry_file, entry_command = entrypoint.detect(box, files)
    profile = ProjectProfile(
        python_version=config.DEFAULT_PYTHON_VERSION,
        deps_file=next((f for f in DEPS_FILES if f in files), None),
        has_tests=any(Path(f).name.startswith("test_") or f.startswith("tests/") for f in files),
        entrypoint=entry_file,
        run_command=entry_command,
        uses_gui=display.detect_gui(box),
    )
    return {"profile": profile}


def plan_run(state: RunState) -> dict:
    """
    1. מקבלת: state (עם profile).
    2. מחזירה: {plan, step_index, success_check}.
    3. עושה: בונה את רשימת הצעדים (התקנת תלויות) ואת בדיקת ההצלחה: הרצת הפרויקט, pytest או קומפילציה.
    """
    profile = state["profile"]
    steps = [Step(command="python --version", purpose="בדיקת הסביבה", in_dockerfile=False)]

    if profile.deps_file == "requirements.txt":
        steps.append(Step(command="pip install -r requirements.txt", purpose="התקנת התלויות"))
    elif profile.deps_file:
        steps.append(Step(command="pip install .", purpose="התקנת הפרויקט ותלויותיו"))

    # מה נחשב "עובד": אם יש בדיקות – שהן נאספות בלי שגיאת import (כמו ב-Repo2Run);
    # אחרת – שנקודת הכניסה רצה; ואם אין כלום – שכל הקבצים מתקמפלים.
    if profile.has_tests:
        steps.append(Step(command="pip install pytest", purpose="כלי הבדיקות"))
        check = SuccessCheck(command="python -m pytest --collect-only -q")
    elif profile.entrypoint:
        check = SuccessCheck(command=entrypoint.run_command_of(profile), kind="run", timeout=config.RUN_CHECK_TIMEOUT)
    else:
        check = SuccessCheck(command="python -m compileall -q .")

    return {"plan": steps, "step_index": 0, "success_check": check}


# ---------- 2. הרצה ----------

def execute_step(state: RunState) -> dict:
    """
    1. מקבלת: state (plan ו-step_index).
    2. מחזירה: {last_result} ובהצלחה גם {step_index} מוגדל ב-1.
    3. עושה: מריצה את הצעד הבא בקונטיינר (כ-root רק אם סומן as_root), ומקדמת את המצביע רק כשהצליח.
    """
    step = state["plan"][state["step_index"]]
    result = _sandbox(state).run(step.command, user="root" if step.as_root else config.CONTAINER_USER)
    update = {"last_result": result}
    if result.ok:
        update["step_index"] = state["step_index"] + 1
    return update


def verify(state: RunState) -> dict:
    """
    1. מקבלת: state (עם success_check).
    2. מחזירה: {last_result}, ובהצלחה גם {status: succeeded} ו-{success_check} חדש במקרה של כלי שורת פקודה.
    3. עושה: מריצה את בדיקת ההצלחה. אם התקבלה שגיאת שימוש של כלי שורת פקודה, בודקת --help ומחשיבה אותו הצלחה.
    """
    check = state["success_check"]
    box = _sandbox(state)
    if check.kind == "run":  # מריצים את הפרויקט עצמו: סקריפט שמסתיים, או שרת שעונה ב-HTTP
        if state["profile"].uses_gui:  # פרויקט עם חלון: מריצים על מסך וירטואלי, וחלון שנשאר פתוח נחשב הצלחה
            result = display.run_gui_check(box, check.command)
        else:
            result = box.run_checked(check.command, timeout=check.timeout)
        if not result.ok and is_usage_error(result):
            # כלי שורת פקודה שדורש ארגומנטים (למשל פקודות משנה). זו לא תקלה: אי אפשר לדעת איזו פקודה להריץ,
            # והרצה אמיתית (כמו אימון) עלולה להיות ארוכה. לכן בודקים --help: אם הוא עובד, הייבואים והפרסור תקינים
            help_check = SuccessCheck(command=f"{check.command} --help", timeout=30, help_only=True)
            help_result = box.run(help_check.command, timeout=help_check.timeout)
            if help_result.ok:
                return {"last_result": help_result, "status": "succeeded", "success_check": help_check}
    else:
        result = box.run(check.command, timeout=check.timeout)
    # נכשל? לא מכריזים "failed" כאן – הניתוב יחליט אם לנסות לתקן או לוותר
    return {"last_result": result, **({"status": "succeeded"} if result.ok else {})}


def is_usage_error(result) -> bool:
    """
    1. מקבלת: result (CommandResult).
    2. מחזירה: bool.
    3. עושה: True אם קוד היציאה 2 והפלט כולל 'usage:' (argparse, click, typer).
    """
    return result.exit_code == 2 and not result.timed_out and "usage:" in result.output.lower()


# ---------- 2.5 אבחון ותיקון (LLM) ----------

def diagnose_error(state: RunState, runtime: Runtime[RunContext]) -> dict:
    """
    1. מקבלת: state (last_result, profile, messages, tool_calls_used) ו-runtime (גרסת הסוכן: v1 או v2).
    2. מחזירה: {messages} וגם {diagnosis} כשהמודל סיכם, או {tool_calls_used} כשביקש כלי.
    3. עושה: סוכן ReAct: המודל חוקר עם כלי קריאה ומסיים בקריאה ל-Diagnosis. רץ שוב ושוב עד שיש אבחון, עד 5 קריאות לכלים.
    """
    used = state.get("tool_calls_used", 0)
    can_investigate = used < config.MAX_TOOL_CALLS
    tools = [*INVESTIGATION_TOOLS, Diagnosis] if can_investigate else [Diagnosis]
    # "required" – חייב לקרוא לכלי; כשנגמר התקציב מכריחים אותו לסכם (Diagnosis בלבד)
    llm = ChatOpenAI(model=config.OPENAI_MODEL).bind_tools(
        tools, tool_choice="required" if can_investigate else "Diagnosis"
    )

    history = state.get("messages", [])
    report_text = prompts.failure_report(state)
    if version_of(runtime.context) == "v2":  # v2: המודל יודע מה כבר נוסה
        report_text += memory.history_text(state.get("attempt_history", []))
    opening = [] if history else [HumanMessage(report_text)]
    response = llm.invoke([SystemMessage(prompts.diagnose_system(version_of(runtime.context))), *history, *opening])

    update: dict = {"messages": [*opening, response]}
    final = next((c for c in response.tool_calls if c["name"] == "Diagnosis"), None)
    if final:
        update["diagnosis"] = Diagnosis(**final["args"])
    else:
        update["tool_calls_used"] = used + len(response.tool_calls)
    return update


def propose_fix(state: RunState, runtime: Runtime[RunContext]) -> dict:
    """
    1. מקבלת: state (עם diagnosis) ו-runtime (שממנו קוראים את גרסת הסוכן: v1 או v2).
    2. מחזירה: {proposed_fix, attempts, attempt_history, tool_calls_used, messages}.
    3. עושה: המודל מציע פקודות תיקון, והניסיון נרשם. לא נוגעת בתוכנית: זה תפקיד apply_fix, אחרי שער הבטיחות.
    """
    llm = ChatOpenAI(model=config.OPENAI_MODEL).with_structured_output(Fix)
    version = version_of(runtime.context)
    tried = state.get("attempt_history", [])
    request = prompts.fix_request(state) + (memory.history_text(tried) if version == "v2" else "")
    messages = [SystemMessage(prompts.fix_system(version)), HumanMessage(request)]
    fix = llm.invoke(messages)
    if version == "v2":  # תיקון שכבר נכשל נחסם ומוחזר למודל עם הסבר
        for _ in range(config.REPEAT_RETRIES):
            if not memory.is_repeat(fix.commands, tried):
                break
            messages = [*messages, HumanMessage(memory.repeat_message(fix.commands))]
            fix = llm.invoke(messages)

    attempt = Attempt(
        number=state.get("attempts", 0) + 1,
        failed_command=state["last_result"].command,
        error=state["last_result"].output[-config.ERROR_EXCERPT_CHARS:],
        category=state["diagnosis"].category,
        fix_commands=fix.commands,
    )
    # ה-diagnosis נשאר ב-State: אם אדם ידחה את התיקון, נצטרך אותו להצעה חדשה
    return {
        "proposed_fix": fix,
        "attempts": attempt.number,
        "attempt_history": [attempt],
        "tool_calls_used": 0,
        "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES)],  # מתחילים חקירה נקייה בכישלון הבא
    }


def switch_python(state: RunState) -> dict:
    """
    1. מקבלת: state (עם diagnosis.python_version).
    2. מחזירה: {container, profile, step_index=0, attempts, attempt_history, ...}.
    3. עושה: יוצרת קונטיינר עם גרסת Python אחרת, מעתיקה אליו את הפרויקט והסודות, מוחקת את הישן, ומריצה את התוכנית מההתחלה.
    """
    target = state["diagnosis"].python_version
    old = _sandbox(state)
    new = Sandbox(python_version=target)
    new.start()
    try:
        old.copy_state_to(new)
    except Exception:
        new.stop()
        raise
    old.stop()

    failed = state["last_result"]
    attempt = Attempt(
        number=state.get("attempts", 0) + 1, failed_command=failed.command,
        error=failed.output[-config.ERROR_EXCERPT_CHARS:],
        category="python_version", fix_commands=[f"switch to Python {target}"],
    )
    return {
        "container": new.name, "profile": state["profile"].model_copy(update={"python_version": target}),
        "step_index": 0,  # מריצים מההתחלה: החבילות צריכות להיות מותקנות מחדש בסביבה החדשה
        "attempts": attempt.number, "attempt_history": [attempt], "diagnosis": None, "tool_calls_used": 0,
        "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES)],
    }


# ---------- 2.6 בטיחות ואישור אדם ----------

def safety_gate(state: RunState, runtime: Runtime[RunContext]) -> dict:
    """
    1. מקבלת: state (עם proposed_fix ו-attempt_history) ו-runtime (גרסת הסוכן).
    2. מחזירה: {fix_risks}: רשימת סיכונים, ריקה אם הכול בטוח.
    3. עושה: מסווגת את פקודות התיקון בקוד קבוע (safety.assess), לא במודל. ב-v2, תיקון שחוזר על ניסיון קודם גם
       אחרי שנחסם, לא רץ לבד: הוא עובר לאישור אדם.
    """
    commands = state["proposed_fix"].commands
    risks = safety.assess(commands)
    earlier = state.get("attempt_history", [])[:-1]  # האחרון ברשימה הוא ההצעה הנוכחית עצמה
    if version_of(runtime.context) == "v2" and memory.is_repeat(commands, earlier):
        risks.append(Risk(kind="repeated", command=" && ".join(commands)))
    return {"fix_risks": risks}


def _approval_request(state: RunState) -> dict:
    """
    1. מקבלת: state.
    2. מחזירה: dict עם kind: secret_needed, sensitive_fix או attempts_exhausted, ופרטי השאלה.
    3. עושה: מחליטה מה לשאול את האדם לפי מה שיש ב-State. הסוד עצמו אף פעם לא נכנס לכאן.
    """
    diagnosis = state.get("diagnosis")
    base = {"container": state["container"]}
    if diagnosis and diagnosis.category == "missing_env_var" and diagnosis.env_var_name and not state.get("proposed_fix"):
        return {**base, "kind": "secret_needed", "env_var": diagnosis.env_var_name, "summary": diagnosis.summary}
    if state.get("fix_risks"):
        fix = state["proposed_fix"]
        return {**base, "kind": "sensitive_fix", "commands": fix.commands, "explanation": fix.explanation,
                "risks": [r.model_dump() for r in state["fix_risks"]]}
    return {**base, "kind": "attempts_exhausted", "attempts": state.get("attempts", 0)}


def human_approval(state: RunState) -> dict:
    """
    1. מקבלת: state.
    2. מחזירה: {decision, approvals} ועדכונים לפי התשובה (נקיון חקירה, הגדלת מגבלה, הערת דחייה).
    3. עושה: עוצרת את הגרף עם interrupt() וממתינה לתשובת אדם; כשמגיעה תשובה, רושמת אותה ביומן ההחלטות.
    הערה: בחידוש הצומת רץ מההתחלה, ולכן כל מה שלפני interrupt חייב להיות בלי תופעות לוואי.
    """
    request = _approval_request(state)
    answer = interrupt(request)
    action, kind = answer["action"], request["kind"]

    detail = {"secret_needed": request.get("env_var", ""),  # שם המשתנה בלבד, לעולם לא הערך
              "sensitive_fix": "; ".join(request.get("commands", [])),
              "attempts_exhausted": str(request.get("attempts", ""))}[kind]
    update: dict = {"decision": action, "approvals": [Approval(kind=kind, action=action, detail=detail)]}

    if kind == "secret_needed" and action == "provided":
        # הסוד כבר נכתב לקונטיינר ע"י הממשק. כאן רק מתחילים מחדש: סופרים ניסיון ומנקים את החקירה
        update |= {"diagnosis": None, "tool_calls_used": 0, "attempts": state.get("attempts", 0) + 1,
                   "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES)]}
    elif kind == "sensitive_fix" and action == "approve" and answer.get("commands"):
        update["proposed_fix"] = Fix(commands=answer["commands"], explanation="נערך ע\"י המשתמש")
    elif kind == "sensitive_fix" and action == "reject":
        update["human_feedback"] = answer.get("note") or "The reviewer rejected this fix."
    elif kind == "attempts_exhausted" and action == "continue":
        update["attempt_limit"] = state.get("attempt_limit", config.MAX_ATTEMPTS) + config.ATTEMPTS_GRANT
    return update


def apply_fix(state: RunState) -> dict:
    """
    1. מקבלת: state (עם proposed_fix).
    2. מחזירה: {plan} מעודכנת, ואיפוס של proposed_fix, fix_risks, diagnosis ו-human_feedback.
    3. עושה: מכניסה את הפקודות המאושרות לפני הצעד שנכשל, כך שירוץ שוב. פקודת מערכת (apt) מסומנת לרוץ כ-root.
    """
    fix = state["proposed_fix"]
    plan, index = state["plan"], state["step_index"]
    fix_steps = []
    for command in fix.commands:
        # פקודת מערכת (apt) עברה אישור אדם, ורק היא רצה כ-root. בקונטיינר אין sudo, לכן מסירים אותו
        is_system = any(r.kind == "system" for r in safety.assess([command]))
        fix_steps.append(Step(command=command.removeprefix("sudo ") if is_system else command,
                              purpose=f"תיקון: {fix.explanation}", is_fix=True, as_root=is_system))
    # אם מה שנכשל הוא עצמו צעד תיקון – מוציאים אותו מהתוכנית, אחרת הוא ירוץ שוב אחרי התיקון הבא
    failed_is_fix = index < len(plan) and plan[index].is_fix
    remaining = plan[index + 1:] if failed_is_fix else plan[index:]
    return {"plan": plan[:index] + fix_steps + remaining, "proposed_fix": None, "fix_risks": [],
            "diagnosis": None, "human_feedback": None}


# ---------- 3. תוצר ----------

def report(state: RunState) -> dict:
    """
    1. מקבלת: state הסופי.
    2. מחזירה: {report, status}.
    3. עושה: בונה את התוצרים (Dockerfile, סקריפט, דוח). הקונטיינר נמחק, חוץ מתצוגה חיה (שרת או חלון בדפדפן):
       אז הוא נשאר פעיל עד שהמשתמשת עוצרת אותו, ונסגר לבד אחרי PREVIEW_TTL_MIN דקות.
    """
    result = artifacts.build_report(state)
    preview = state.get("preview")
    if preview and preview.kind in ("web", "desktop"):
        _sandbox(state).stop_later(config.PREVIEW_TTL_MIN * 60)
    else:
        _sandbox(state).stop()
    return {"report": result, "status": "succeeded" if result.succeeded else "failed"}
