"""צמתי בדיקת הפקודות והתצוגה. שניהם קוד דטרמיניסטי, בלי מודל.

smoke_test:    מריץ כל פקודת משנה כמה שניות ובודק שהיא לא נשברה בגלל הסביבה (ומוצא איזו פקודה פותחת חלון).
open_preview:  מכין למשתמשת תצוגה של הפרויקט: דפדפן חי (שרת או חלון) או הקלטת וידאו, לפי מה שבחרה בהתחלה.
"""
from reporunner import config, display, smoke
from reporunner.artifacts import SERVER_PORT, parse_cli_help
from reporunner.models import Preview
from reporunner.sandbox import Sandbox
from reporunner.state import RunState

SETTLE_SECONDS = 3  # כמה זמן נותנים לחלון להיפתח לפני שמקליטים


def _box(state: RunState) -> Sandbox:
    """
    1. מקבלת: state.
    2. מחזירה: Sandbox מחובר לקונטיינר של הריצה.
    3. עושה: מתחברת מחדש לקונטיינר לפי השם ששמור ב-State.
    """
    return Sandbox.attach(state["container"])


def needs_smoke(state: RunState) -> bool:
    """
    1. מקבלת: state (אחרי אימות שהצליח).
    2. מחזירה: bool.
    3. עושה: True אם כדאי להריץ בדיקת פקודות: כלי עם פקודות משנה (אומת רק ב---help) או פרויקט עם חלון.
    """
    check = state.get("success_check")
    profile = state.get("profile")
    return bool((check and check.help_only) or (profile and profile.uses_gui))


def wants_preview(state: RunState) -> bool:
    """
    1. מקבלת: state.
    2. מחזירה: bool.
    3. עושה: True אם המשתמשת ביקשה תצוגה חיה או הקלטה.
    """
    return state.get("preview_mode", "none") != "none"


def smoke_test(state: RunState) -> dict:
    """
    1. מקבלת: state (אחרי verify שהצליח: profile, success_check, last_result).
    2. מחזירה: בהצלחה {status: succeeded, preview_command}; בכשל סביבה {status: running, last_result} כדי שהאבחון יטפל.
    3. עושה: מריצה כל פקודת משנה כמה שניות (על מסך וירטואלי אם יש חלון). פקודה שנשברה בגלל הסביבה (ייבוא, ספרייה, מסך)
       נחשבת כשל; פקודה שעדיין רצה בסוף הזמן (אימון, חלון) נחשבת תקינה. מבין אלה, הראשונה שפותחת חלון על המסך הווירטואלי (נבדק בפועל) נשמרת לתצוגה.
    """
    box = _box(state)
    profile = state["profile"]
    check = state["success_check"]
    subcommands = list(parse_cli_help(state["last_result"].output)) if check.help_only else []

    if profile.uses_gui:
        install = display.install_display_stack(box)
        if not install.ok:
            return {"last_result": install, "status": "running"}
        display.start_display(box)

    environment = f"DISPLAY={config.DISPLAY} " if profile.uses_gui else ""
    preview_command = None
    for command in smoke.smoke_commands(check.command, subcommands):
        result = box.run(environment + command, timeout=config.SMOKE_TIMEOUT_SEC)
        outcome = smoke.classify_smoke(result)
        if outcome == "broken":
            return {"last_result": result.model_copy(update={"command": command}), "status": "running"}
        if outcome == "alive" and profile.uses_gui and preview_command is None and display.opens_window(box, command):
            preview_command = command
    return {"status": "succeeded", "preview_command": preview_command}


def open_preview(state: RunState) -> dict:
    """
    1. מקבלת: state (עם preview_mode, preview_command או פורט של שרת).
    2. מחזירה: {preview}: Preview עם כתובת בדפדפן או קובץ הקלטה, או None אם אין מה להציג.
    3. עושה: חלון: מפעילה אותו על מסך וירטואלי ומחברת noVNC (חי), או מקליטה כמה שניות (הקלטה). שרת: מפעילה אותו
       ומעבירה פורט למארח. פרויקט שאין בו מה להציג (כלי שורת פקודה בלי חלון) לא מקבל תצוגה.
    """
    box = _box(state)
    recording = state.get("preview_mode") == "recording"
    command = state.get("preview_command")

    if command:
        display.install_display_stack(box, live=not recording, recording=recording)
        display.start_display(box)
        if recording:
            display.launch_gui(box, command)
            box.run(f"sleep {SETTLE_SECONDS}", timeout=SETTLE_SECONDS + 10)
            display.record(box, state["container"])
            return {"preview": Preview(kind="recording", url=f"/reporunner/recording/{state['container']}",
                                       note=f"הקלטה של {config.RECORD_SECONDS} שניות")}
        host_port = display.start_vnc(box)
        display.launch_gui(box, command)
        return {"preview": Preview(kind="desktop", url=display.desktop_url(host_port), note="החלון רץ בקונטיינר ומוצג בדפדפן")}

    match = SERVER_PORT.search(state["last_result"].output)
    if not match:
        return {"preview": None}
    host_port = display.launch_web(box, state["success_check"].command, int(match.group(1)))
    note = "הקלטה זמינה רק לפרויקט עם חלון, לכן הוצג שרת חי" if recording else "השרת רץ בקונטיינר"
    return {"preview": Preview(kind="web", url=f"http://localhost:{host_port}", note=note)}

