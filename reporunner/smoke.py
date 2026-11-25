"""בדיקת פקודות קצרה: מריצים כל פקודת משנה של הפרויקט כמה שניות ובודקים אם נשברה בגלל הסביבה.

למה: אימות ב---help בודק רק שהפרסור עובד. ייבוא עצל (למשל tkinter בתוך פקודת watch) מתגלה רק כשהפקודה באמת רצה.
כל ההחלטות כאן בקוד דטרמיניסטי, בלי מודל.
"""
import re
from typing import Literal

from reporunner.models import CommandResult

SmokeOutcome = Literal["alive", "ok", "needs_args", "needs_input", "broken"]

# שגיאות שמעידות על סביבה שבורה (ולא על חוסר קלט): חבילה, ספרייה משותפת או מסך
ENVIRONMENT_ERROR = re.compile(
    r"ModuleNotFoundError|ImportError|TclError|couldn't connect to display|no display name|"
    r"cannot open shared object|libGL|Xlib\.error|pygame\.error: No available video device",
    re.IGNORECASE,
)


def classify_smoke(result: CommandResult) -> SmokeOutcome:
    """
    1. מקבלת: result (תוצאת הרצה קצרה של פקודה).
    2. מחזירה: alive (עדיין רצה כשנגמר הזמן, למשל אימון או חלון), ok (הסתיימה בהצלחה), needs_args (חסרים ארגומנטים),
       needs_input (נעצרה כי חסר קלט כמו קובץ שמור, לא בגלל הסביבה), או broken (נשברה בגלל הסביבה).
    3. עושה: מסווגת לפי קוד יציאה ופלט. רק broken נחשב כשל שהסוכן צריך לתקן.
    """
    if result.timed_out:
        return "alive"
    if result.ok:
        return "ok"
    output = result.output
    if result.exit_code == 2 and "usage:" in output.lower():
        return "needs_args"
    if ENVIRONMENT_ERROR.search(output):
        return "broken"
    return "needs_input"


def base_command(check_command: str) -> str:
    """
    1. מקבלת: check_command (פקודת האימות, למשל 'python main.py --help').
    2. מחזירה: הפקודה בלי הדגל --help.
    3. עושה: מוצאת את פקודת הבסיס של הפרויקט, שאליה מוסיפים פקודת משנה.
    """
    return re.sub(r"\s+--help\s*$", "", check_command).strip()


def smoke_commands(check_command: str, subcommands: list[str]) -> list[str]:
    """
    1. מקבלת: check_command ו-subcommands (פקודות המשנה שנמצאו ב---help, ריק אם אין).
    2. מחזירה: רשימת הפקודות להריץ בבדיקה.
    3. עושה: לכל פקודת משנה בונה פקודה מלאה; בלי פקודות משנה, מריצה את הפרויקט עצמו.
    """
    base = base_command(check_command)
    return [f"{base} {name}" for name in subcommands] or [base]
