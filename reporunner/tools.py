"""כלי החקירה של הסוכן. כולם **קריאה בלבד**, ולכן לא עוברים בשער הבטיחות.

הכלים מקבלים את ה-State דרך InjectedState: LangGraph מזריק אותו אוטומטית,
והמודל לא רואה את הפרמטר הזה (הוא לא חלק מהסכמה שנשלחת אליו). כך הכלי יודע באיזה קונטיינר לעבוד.
"""
import shlex
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from reporunner.sandbox import Sandbox

TOOL_TIMEOUT_SEC = 30
MAX_READ_BYTES = 6000


def _allowed(path: str) -> bool:
    """
    1. מקבלת: path: נתיב שביקש המודל.
    2. מחזירה: bool.
    3. עושה: מאשרת רק נתיב יחסי בתוך הפרויקט: בלי '/' בהתחלה ובלי '..'.
    """
    return not path.startswith("/") and ".." not in path.split("/")


def _run_readonly(state: dict, command: str) -> str:
    """
    1. מקבלת: state (עם container) ו-command (פקודת קריאה בלבד).
    2. מחזירה: מחרוזת: הפלט, או הודעת השגיאה.
    3. עושה: מריצה פקודה בקונטיינר עם הגבלת זמן של 30 שניות, עבור כלי החקירה.
    """
    result = Sandbox.attach(state["container"]).run(command, timeout=TOOL_TIMEOUT_SEC)
    return result.stdout if result.ok else (result.stderr or result.stdout or f"exit code {result.exit_code}")


# 1. מקבלת: state (מוזרק אוטומטית, המודל לא רואה אותו) ו-path.
# 2. מחזירה: מחרוזת: רשימת הקבצים בתוך תגית <result>.
# 3. עושה: מציגה את תוכן תיקייה בפרויקט (קריאה בלבד).
@tool
def list_files(state: Annotated[dict, InjectedState], path: str = ".") -> str:
    """List files and folders in a directory of the project (relative path, default '.')."""
    if not _allowed(path):
        return "Error: path must be relative and inside the project."
    return f"<result>\n{_run_readonly(state, f'ls -la -- {shlex.quote(path)}')}\n</result>"


# 1. מקבלת: state (מוזרק) ו-path.
# 2. מחזירה: מחרוזת: תחילת הקובץ בתוך <file>.
# 3. עושה: קוראת קובץ מהפרויקט (קריאה בלבד, עד 6,000 תווים).
@tool
def read_file(state: Annotated[dict, InjectedState], path: str) -> str:
    """Read the beginning of a text file in the project (relative path)."""
    if not _allowed(path):
        return "Error: path must be relative and inside the project."
    content = _run_readonly(state, f"head -c {MAX_READ_BYTES} -- {shlex.quote(path)}")
    return f'<file path="{path}">\n{content}\n</file>'


# 1. מקבלת: state (מוזרק), pattern ו-path.
# 2. מחזירה: מחרוזת: עד 30 שורות תואמות בתוך <result>.
# 3. עושה: מחפשת טקסט בקבצי הפרויקט (grep, קריאה בלבד).
@tool
def search_text(state: Annotated[dict, InjectedState], pattern: str, path: str = ".") -> str:
    """Search for a text pattern (grep) inside project files. Returns up to 30 matching lines."""
    if not _allowed(path):
        return "Error: path must be relative and inside the project."
    command = f"grep -rnI --exclude-dir=.git -- {shlex.quote(pattern)} {shlex.quote(path)} | head -n 30"
    return f"<result>\n{_run_readonly(state, command) or 'no matches'}\n</result>"


INVESTIGATION_TOOLS = [list_files, read_file, search_text]
