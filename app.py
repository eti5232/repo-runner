"""ממשק RepoRunner (Streamlit).

הרצה:  streamlit run app.py

הממשק מדבר ישירות עם הגרף של LangGraph (אותו גרף שמשמש את ה-CLI), ולכן עצירות לאישור,
שמירת מצב והמשך עובדים בדיוק אותו דבר: אפשר להתחיל בדפדפן ולהמשיך מהטרמינל עם --resume.
"""
import html
import re
import sqlite3
import uuid

import streamlit as st
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from cli import RISK_LABELS, describe, save_report
from reporunner import config
from reporunner.graph import build_graph
from reporunner.models import checkpoint_serializer
from reporunner.sandbox import Sandbox

FIXTURES = sorted(p.name for p in (config.PROJECT_ROOT / "evaluation" / "fixtures").iterdir() if p.is_dir())

# שם קצר בעברית לכל צומת בגרף (מוצג בשורת ההתקדמות ובכרטיסי האירועים)
NODE_LABELS = {
    "clone_repo": "שכפול", "analyze_project": "ניתוח", "plan_run": "תוכנית", "execute_step": "הרצה",
    "verify": "אימות", "report": "תוצרים", "diagnose_error": "אבחון", "investigate": "חקירה",
    "propose_fix": "הצעת תיקון", "safety_gate": "שער בטיחות", "human_approval": "אישור אדם",
    "apply_fix": "החלת תיקון", "switch_python": "החלפת Python",
}
MAIN_FLOW = ["clone_repo", "analyze_project", "plan_run", "execute_step", "verify", "report"]
REPAIR_LOOP = ["diagnose_error", "investigate", "propose_fix", "safety_gate", "human_approval", "apply_fix", "switch_python"]

STYLE = """
<style>
:root { --bg:#0b1220; --card:#111a2e; --line:#22304d; --text:#e2e8f0; --muted:#8aa0c0;
        --teal:#14b8a6; --amber:#f59e0b; --red:#ef4444; --green:#22c55e; }
.stApp { background: radial-gradient(1200px 600px at 85% -10%, #12324a 0%, var(--bg) 55%); color: var(--text); }
html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] { direction: rtl; }
[data-testid="stHeader"] { background: transparent; }
h1, h2, h3, p, label, .stMarkdown { text-align: right; }
pre, code, .stCode, textarea, input[type="text"] { direction: ltr; text-align: left; }
.tag { margin-right: 8px; padding: 1px 9px; border-radius: 999px; font-size: 11px; direction: ltr; display: inline-block;
       color: var(--teal); border: 1px solid rgba(20,184,166,.45); }
.event .body.ltr { direction: ltr; text-align: left; }

.hero { padding: 38px 40px; border-radius: 22px; margin-bottom: 22px; border: 1px solid var(--line);
        background: linear-gradient(135deg, rgba(20,184,166,.18), rgba(17,26,46,.9) 55%); }
.hero h1 { direction: ltr; text-align: right; font-size: 54px; margin: 6px 0 4px; letter-spacing: -1px; color: #fff; }
.hero p { color: var(--muted); font-size: 18px; margin: 0; max-width: 760px; }
.badge { display: inline-block; padding: 4px 12px; border-radius: 999px; font-size: 12px; direction: ltr;
         color: var(--teal); border: 1px solid rgba(20,184,166,.45); background: rgba(20,184,166,.08); }

.flow { margin: 6px 0 4px; }
.flow-title { color: var(--muted); font-size: 12px; margin: 10px 0 6px; }
.chip { display: inline-block; margin: 3px 0 3px 8px; padding: 6px 14px; border-radius: 999px; font-size: 13px;
        color: #5d7291; border: 1px solid var(--line); background: rgba(17,26,46,.6); }
.chip.done { color: var(--text); border-color: rgba(20,184,166,.55); background: rgba(20,184,166,.12); }
.chip.human.done { border-color: rgba(245,158,11,.7); background: rgba(245,158,11,.14); color: #fde7b0; }
.chip.now { color: #04201d; background: var(--teal); border-color: var(--teal); font-weight: 700;
            animation: pulse 1.4s ease-in-out infinite; }
@keyframes pulse { 0%,100% { box-shadow: 0 0 0 0 rgba(20,184,166,.5); } 50% { box-shadow: 0 0 0 7px rgba(20,184,166,0); } }

.meta { color: var(--muted); font-size: 13px; margin: 6px 0; }
.meta .ltr { direction: ltr; unicode-bidi: embed; }
.event { border: 1px solid var(--line); background: var(--card); border-radius: 14px; padding: 10px 14px; margin: 8px 0; }
.event .head { display: flex; align-items: center; gap: 10px; color: var(--muted); font-size: 12px; }
.dot { width: 9px; height: 9px; border-radius: 50%; background: var(--teal); display: inline-block; }
.dot.fail { background: var(--red); } .dot.human { background: var(--amber); }
.event .body { margin-top: 6px; font-size: 14px; white-space: pre-wrap; word-break: break-word; }
.event .body.code { direction: ltr; text-align: left; font-family: Consolas, monospace; font-size: 12.5px; color: #c7d2e6; }

.human-title { font-size: 20px; font-weight: 700; color: var(--amber); margin-bottom: 6px; }
.risk { display: inline-block; margin: 2px 0 2px 8px; padding: 3px 10px; border-radius: 8px; font-size: 12px;
        color: #fecaca; background: rgba(239,68,68,.14); border: 1px solid rgba(239,68,68,.4); }
.result { border-radius: 16px; padding: 18px 22px; margin: 10px 0 16px; font-size: 20px; font-weight: 700; }
.result.ok { background: rgba(34,197,94,.12); border: 1px solid rgba(34,197,94,.5); color: #bbf7d0; }
.result.bad { background: rgba(239,68,68,.12); border: 1px solid rgba(239,68,68,.5); color: #fecaca; }
div[data-testid="stMetric"] { background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 12px 16px; }
.stButton > button { border-radius: 10px; }
</style>
"""


# ---------- חיבור לגרף ----------

@st.cache_resource
def get_graph():
    """
    1. מקבלת: כלום.
    2. מחזירה: גרף LangGraph.
    3. עושה: יוצרת גרף אחד לכל השרת, עם שמירת מצב באותו קובץ שבו משתמש ה-CLI (cache_resource).
    """
    config.CHECKPOINT_DB.parent.mkdir(exist_ok=True)
    connection = sqlite3.connect(str(config.CHECKPOINT_DB), check_same_thread=False)
    return build_graph(SqliteSaver(connection, serde=checkpoint_serializer()))


def new_run(source: str, commit: str | None) -> None:
    """
    1. מקבלת: source ו-commit.
    2. מחזירה: כלום.
    3. עושה: פותחת ריצה חדשה ב-session_state וקובעת את הקלט להרצה.
    """
    st.session_state.run = {
        "thread": uuid.uuid4().hex[:8], "source": source, "events": [], "visited": [], "running": False,
        "pending": None, "report": None, "folder": None, "error": None,
    }
    st.session_state.drive_input = {"source": source, "commit": commit or None}


def drive(graph_input, flow_slot, timeline_slot) -> None:
    """
    1. מקבלת: graph_input, flow_slot, timeline_slot.
    2. מחזירה: כלום.
    3. עושה: מריצה את הגרף עד סיום או עצירה לאישור, ומעדכנת את המסך אחרי כל צומת. שגיאה מוצגת ולא מקריסה.
    """
    run = st.session_state.run
    run_config = {"configurable": {"thread_id": run["thread"]}, "recursion_limit": config.RECURSION_LIMIT}
    run.update(pending=None, running=True, error=None)
    try:
        for update in get_graph().stream(graph_input, run_config, stream_mode="updates"):
            if "__interrupt__" in update:
                run["pending"] = update["__interrupt__"][0].value
                continue
            for node, change in update.items():
                run["visited"].append(node)
                run["events"].append((node, describe(node, change)))
                if "report" in change:
                    run["report"] = change["report"]
                    run["folder"] = save_report(change["report"], run["thread"], run["source"])
                draw_flow(flow_slot, run)
                draw_timeline(timeline_slot, run)
    except Exception as exc:  # הממשק לא קורס: מציג את השגיאה
        run["error"] = f"{type(exc).__name__}: {exc}"
    run["running"] = False


def resume(answer: dict) -> None:
    """
    1. מקבלת: answer: תשובת האדם.
    2. מחזירה: כלום.
    3. עושה: קובעת הרצה מחדש עם Command(resume=answer) ומרעננת את הדף.
    """
    st.session_state.drive_input = Command(resume=answer)
    st.rerun()


# ---------- ציור ----------

def draw_flow(slot, run: dict) -> None:
    """
    1. מקבלת: slot ו-run.
    2. מחזירה: כלום.
    3. עושה: מצייר את שורת ההתקדמות: אילו צמתים הושלמו ואיזה פועל עכשיו.
    """
    visited = set(run["visited"])
    current = run["visited"][-1] if run["running"] and run["visited"] else None

    def chips(nodes):
        """
        1. מקבלת: nodes: רשימת צמתים.
        2. מחזירה: מחרוזת HTML של תגיות.
        3. עושה: בונה תגית לכל צומת לפי מצבו (הושלם, פועל, אישור אדם).
        """
        return "".join(
            f'<span class="chip{" done" if n in visited else ""}{" now" if n == current else ""}'
            f'{" human" if n == "human_approval" else ""}">{NODE_LABELS[n]}</span>'
            for n in nodes
        )

    slot.markdown(
        f'<div class="flow"><div class="flow-title">הזרימה הראשית</div>{chips(MAIN_FLOW)}'
        f'<div class="flow-title">לולאת האבחון והתיקון</div>{chips(REPAIR_LOOP)}</div>',
        unsafe_allow_html=True,
    )


def draw_timeline(slot, run: dict) -> None:
    """
    1. מקבלת: slot ו-run.
    2. מחזירה: כלום.
    3. עושה: מצייר כרטיס לכל אירוע בריצה, עם בריחה של HTML כדי שפלט של פרויקט לא יוכל להזריק קוד.
    """
    cards = []
    for node, text in run["events"]:
        failed = text.startswith("✘")
        kind = "fail" if failed else "human" if node in ("human_approval", "safety_gate") else ""
        code = " code" if node in ("execute_step", "verify", "propose_fix") else ""
        tag = ""
        if node == "propose_fix":  # בכרטיס קוד מציגים רק את הפקודות, בלי קידומת בעברית שמתערבבת בכיוון הטקסט
            text = text.removeprefix("תיקון מוצע: ")
        diagnosis = re.match(r"אבחון \[(\w+)\]: (.*)", text, re.S)
        if node == "diagnose_error" and diagnosis:  # הקטגוריה כתגית, והסיכום באנגלית בבלוק נפרד (בלי ערבוב כיוונים)
            tag, text, code = f'<span class="tag">{html.escape(diagnosis.group(1))}</span>', diagnosis.group(2), " ltr"
        cards.append(
            f'<div class="event"><div class="head"><span class="dot {kind}"></span>{NODE_LABELS[node]}{tag}</div>'
            f'<div class="body{code}" dir="auto">{html.escape(text or "הושלם")}</div></div>'
        )
    slot.markdown(f'<div class="timeline">{"".join(cards)}</div>', unsafe_allow_html=True)


def draw_approval(run: dict) -> None:
    """
    1. מקבלת: run.
    2. מחזירה: כלום.
    3. עושה: מציגה את חלונית האישור לפי סוג העצירה (סוד, תיקון רגיש, נגמרו ניסיונות), וכפתורי ההחלטה.
    """
    request = run["pending"]
    if not request:
        return
    key = f"{run['thread']}-{len(run['events'])}"
    kind = request["kind"]
    with st.container(border=True):
        st.markdown('<div class="human-title">הסוכן עצר וממתין להחלטה שלך</div>', unsafe_allow_html=True)

        if kind == "secret_needed":
            name = request["env_var"]
            st.write(f"הפרויקט דורש את משתנה הסביבה **{name}**.")
            st.markdown(f'<div class="meta"><span class="ltr">{html.escape(request["summary"])}</span></div>',
                        unsafe_allow_html=True)
            st.caption("הערך נכתב ישירות לקונטיינר. הוא לא נשמר במצב הריצה ולא נשלח ל-LangSmith.")
            with st.form(f"secret-{key}", clear_on_submit=True):
                value = st.text_input(f"ערך ל-{name}", type="password")
                save, dummy = st.columns(2)
                if save.form_submit_button("שמור והמשך", type="primary") and value:
                    Sandbox.attach(request["container"]).set_secret(name, value)
                    resume({"action": "provided"})
                if dummy.form_submit_button("השתמש בערך דמה"):
                    Sandbox.attach(request["container"]).set_secret(name, "dummy-value")
                    resume({"action": "provided"})

        elif kind == "sensitive_fix":
            st.write("הסוכן מציע תיקון שדורש את אישורך:")
            st.markdown(f'<div class="meta"><span class="ltr">{html.escape(request["explanation"])}</span></div>',
                        unsafe_allow_html=True)
            st.markdown("".join(f'<span class="risk">{RISK_LABELS[r["kind"]]}</span>' for r in request["risks"]),
                        unsafe_allow_html=True)
            st.code("\n".join(request["commands"]), language="bash")
            note = st.text_input("סיבה לדחייה (לא חובה)", key=f"note-{key}")
            approve, reject, stop = st.columns(3)
            if approve.button("אשר והרץ", type="primary", key=f"yes-{key}", use_container_width=True):
                resume({"action": "approve"})
            if reject.button("דחה והצע אחר", key=f"no-{key}", use_container_width=True):
                resume({"action": "reject", "note": note})
            if stop.button("עצור", key=f"stop-{key}", use_container_width=True):
                resume({"action": "stop"})

        else:  # attempts_exhausted
            st.write(f"נוסו {request['attempts']} תיקונים והפרויקט עדיין לא רץ.")
            more, stop = st.columns(2)
            if more.button(f"המשך ({config.ATTEMPTS_GRANT} ניסיונות נוספים)", type="primary", key=f"more-{key}",
                           use_container_width=True):
                resume({"action": "continue"})
            if stop.button("עצור", key=f"stop-{key}", use_container_width=True):
                resume({"action": "stop"})

        st.caption("אפשר גם להמשיך מהטרמינל:")
        st.code(f"python cli.py --resume --thread {run['thread']}", language="bash")


def draw_report(run: dict) -> None:
    """
    1. מקבלת: run.
    2. מחזירה: כלום.
    3. עושה: מציגה את התוצאה: באנר, מדדים, בורר פקודות לכלי שורת פקודה, ולשוניות Dockerfile, run.sh ומה תוקן.
    """
    report = run["report"]
    if not report:
        return
    css, text = ("ok", "הפרויקט רץ") if report.succeeded else ("bad", "הפרויקט לא רץ")
    st.markdown(f'<div class="result {css}">{text}</div>', unsafe_allow_html=True)
    a, b, c, d = st.columns(4)
    a.metric("גרסת Python", report.python_version)
    b.metric("תיקונים", len(report.fixes))
    c.metric("פורט", report.port or "–")
    d.metric("משתני סביבה", len(report.env_vars))
    st.write(report.summary)
    if report.help_only:
        st.info("הפרויקט הוא כלי שורת פקודה והוא תקין (אומת ב---help). לא הורצה פקודה ממשית, "
                "כי היא עלולה להיות ארוכה או לדרוש משאבים. בחרי איזו פקודה להריץ:")
        if report.cli_commands:
            choice = st.radio(
                "פקודה", report.cli_commands, horizontal=True, key=f"cmd-{run['thread']}",
                format_func=lambda name: f"{name}  ·  {report.cli_help[name]}" if report.cli_help.get(name) else name,
            )
            st.caption("במחשב שלך, מתיקיית הפרויקט (מומלץ לפקודה שפותחת חלון, כמו watch):")
            st.code(f"{report.run_command} {choice}", language="bash")
            st.caption("או ב-Docker (בלי חלון גרפי):")
            st.code(f"docker build -t myproject .\ndocker run --rm myproject {choice}", language="bash")

    tab_docker, tab_script, tab_fixes = st.tabs(["Dockerfile", "run.sh", "מה תוקן"])
    with tab_docker:
        st.code(report.dockerfile, language="dockerfile")
        st.download_button("הורדת Dockerfile", report.dockerfile, file_name="Dockerfile")
    with tab_script:
        st.code(report.run_script, language="bash")
        st.download_button("הורדת run.sh", report.run_script, file_name="run.sh")
    with tab_fixes:
        if not report.fixes:
            st.write("לא נדרשו תיקונים.")
        for line in report.fixes:  # בלוק קוד (משמאל לימין): שורה שמערבבת עברית ופקודות קריאה יותר כך
            st.code(line, language=None)
    if run["folder"]:
        st.markdown(f'<div class="meta">התוצרים נשמרו גם ב: <span class="ltr">{html.escape(str(run["folder"]))}</span></div>',
                    unsafe_allow_html=True)


# ---------- העמוד ----------

st.set_page_config(page_title="RepoRunner", page_icon="🏃", layout="wide")
st.markdown(STYLE, unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### RepoRunner")
    st.caption("סוכן שמריץ, מאבחן ומתקן פרויקטים עד שהם עובדים.")
    st.markdown(f"**מודל:** `{config.OPENAI_MODEL}`  \n**מגבלת ניסיונות:** {config.MAX_ATTEMPTS}  \n**תמונת בסיס:** python:{config.DEFAULT_PYTHON_VERSION}-slim")
    st.divider()
    st.caption("כל הפקודות רצות בקונטיינר Docker מבודד. פעולה רגישה תמיד עוצרת לאישור שלך.")
    if st.button("ריצה חדשה", use_container_width=True):
        st.session_state.pop("run", None)
        st.rerun()

st.markdown(
    '<div class="hero"><span class="badge">LangGraph · LangSmith · Docker</span><h1>RepoRunner</h1>'
    "<p>הדביקו קישור ל-GitHub או בחרו פרויקט לדוגמה, והסוכן יריץ אותו, יאבחן שגיאות, יתקן, "
    "ויחזיר Dockerfile שעובד. כל פעולה רגישה עוצרת לאישור שלכם.</p></div>",
    unsafe_allow_html=True,
)

with st.container(border=True):
    left, right = st.columns([3, 2])
    source = left.text_input("קישור GitHub או נתיב לתיקייה", placeholder="https://github.com/user/repo")
    example = right.selectbox("או פרויקט לדוגמה", [""] + FIXTURES, format_func=lambda n: n or "בחרו דוגמה")
    commit = st.text_input("Commit מסוים (לא חובה)")
    if st.button("הרץ", type="primary", use_container_width=True):
        target = source.strip() or (str(config.PROJECT_ROOT / "evaluation" / "fixtures" / example) if example else "")
        if target:
            new_run(target, commit.strip())
        else:
            st.warning("הזינו קישור, או בחרו פרויקט לדוגמה.")

run = st.session_state.get("run")
if run:
    st.markdown(f'<div class="meta">ריצה <span class="ltr">{run["thread"]}</span> · '
                f'<span class="ltr">{html.escape(run["source"])}</span></div>', unsafe_allow_html=True)
    flow_slot = st.empty()
    approval_slot = st.container()
    timeline_slot = st.empty()

    graph_input = st.session_state.pop("drive_input", None)
    if graph_input is not None:
        drive(graph_input, flow_slot, timeline_slot)
    draw_flow(flow_slot, run)
    draw_timeline(timeline_slot, run)

    if run["error"]:
        st.error(run["error"])
    with approval_slot:
        draw_approval(run)
    draw_report(run)
