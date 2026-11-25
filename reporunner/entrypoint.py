"""זיהוי נקודת הכניסה של הפרויקט: איזה קובץ מריצים, ובאיזו פקודה.

הסדר (הכול בקוד דטרמיניסטי, בלי מודל):
  1. פרויקט של Streamlit או Chainlit: מזהים לפי הייבוא, והפקודה היא `streamlit run ...` או `chainlit run ...`
     (אפליקציות כאלה לא מורצות עם `python קובץ.py`).
  2. שם מוכר: main.py, app.py, run.py, cli.py.
  3. קובץ עם `if __name__ == "__main__"`: אם יש כמה, בוחרים את זה ששמו הכי מתאים להרצה.
"""
import re
import shlex
from typing import Protocol

from reporunner.models import ProjectProfile

KNOWN_NAMES = ("main.py", "app.py", "run.py", "cli.py")  # לפי סדר עדיפות

# הפקודה שמריצה אפליקציה של כל מסגרת. הפורט נקבע ע"י המסגרת, ובדיקת ההצלחה מוצאת אותו לבד
FRAMEWORK_COMMANDS = {
    "streamlit": "streamlit run {file} --server.headless true",
    "chainlit": "chainlit run {file} --headless",
}

# מילים בשם קובץ שמרמזות שזה קובץ ההרצה, או שלא
GOOD_WORDS = ("app", "main", "server", "serve", "run", "start", "chat", "cli", "gui", "game", "play", "web")
BAD_WORDS = ("test", "build", "add", "setup", "index", "migrate", "seed", "install", "config", "common", "util",
             "helper", "guard", "conftest", "benchmark")

MAX_DEPTH = 1  # רק קבצים בתיקייה הראשית או בתת-תיקייה אחת


class Runner(Protocol):
    """כל מה שיודע להריץ פקודה ולהחזיר פלט (Sandbox, או דמה בבדיקות)."""

    def run(self, command: str, **kwargs): ...


def score(path: str) -> int:
    """
    1. מקבלת: path (נתיב של קובץ פייתון בפרויקט).
    2. מחזירה: ציון: ככל שגבוה יותר, סביר יותר שזה קובץ ההרצה.
    3. עושה: נותנת נקודות למילים כמו app/server/chat בשם, מורידה על test/build/setup, ומעדיפה קבצים בתיקייה הראשית.
    """
    name = path.rsplit("/", 1)[-1].lower()
    points = 10 if name in KNOWN_NAMES else 0
    points += 2 * sum(word in name for word in GOOD_WORDS)
    points -= 3 * sum(word in name for word in BAD_WORDS)
    return points - 2 * path.count("/")


def choose(paths: list[str]) -> str | None:
    """
    1. מקבלת: paths (רשימת קבצי פייתון מועמדים).
    2. מחזירה: הקובץ המתאים ביותר, או None אם הרשימה ריקה.
    3. עושה: בוחרת לפי הציון, ובשוויון את הקצר ואז לפי סדר האלף-בית, כדי שהתוצאה תהיה תמיד זהה.
    """
    return max(paths, key=lambda path: (score(path), -len(path), path), default=None) if paths else None


def pick(files: set[str], framework_files: dict[str, list[str]], main_files: list[str]) -> tuple[str | None, str | None]:
    """
    1. מקבלת: files (קבצי הפרויקט), framework_files (לכל מסגרת: הקבצים שמייבאים אותה), main_files (קבצים עם __main__).
    2. מחזירה: (קובץ הכניסה, פקודת הרצה מפורשת או None אם מספיק `python קובץ`).
    3. עושה: בוחרת לפי הסדר: מסגרת מזוהה, שם מוכר, קובץ עם __main__.
    """
    for framework, command in FRAMEWORK_COMMANDS.items():
        entry = choose(framework_files.get(framework, []))
        if entry:
            return entry, command.format(file=shlex.quote(entry))
    known = next((name for name in KNOWN_NAMES if name in files), None)
    if known:
        return known, None
    return choose(main_files), None


# ---------- חיפוש בתוך הקונטיינר ----------

FRAMEWORK_IMPORT = r"^[[:space:]]*(import|from)[[:space:]]+(streamlit|chainlit)\b"
MAIN_GUARD = r"__name__[[:space:]]*==[[:space:]]*.__main__."
_GREP_HIT = re.compile(r"^\./(?P<path>.+?):\s*(?:import|from)\s+(?P<framework>streamlit|chainlit)\b")


def _shallow(path: str) -> bool:
    """
    1. מקבלת: path (נתיב יחסי).
    2. מחזירה: bool.
    3. עושה: True אם הקובץ בתיקייה הראשית או בתת-תיקייה אחת (לא עמוק בתוך ספריות).
    """
    return path.count("/") <= MAX_DEPTH


def detect(box: Runner, files: set[str]) -> tuple[str | None, str | None]:
    """
    1. מקבלת: box (קונטיינר עם הפרויקט) ו-files (קבצי הפרויקט).
    2. מחזירה: (קובץ הכניסה, פקודת הרצה מפורשת או None).
    3. עושה: מחפשת בקבצי הפייתון של הפרויקט מסגרות (Streamlit, Chainlit) וקבצים עם __main__, ובוחרת לפי pick.
    """
    hits = box.run(f"grep -rEoH --include='*.py' '{FRAMEWORK_IMPORT}' . | head -60").stdout.splitlines()
    framework_files: dict[str, list[str]] = {}
    for line in hits:
        match = _GREP_HIT.match(line)
        if match and _shallow(match["path"]):
            framework_files.setdefault(match["framework"], []).append(match["path"])
    top_level = box.run(f"grep -lE --include='*.py' '{MAIN_GUARD}' *.py 2>/dev/null | head -30").stdout.splitlines()
    return pick(files, framework_files, [path for path in top_level if path.endswith(".py")])


def run_command_of(profile: ProjectProfile) -> str | None:
    """
    1. מקבלת: profile.
    2. מחזירה: הפקודה שמריצה את הפרויקט, או None אם אין נקודת כניסה.
    3. עושה: מחזירה את הפקודה המפורשת (למסגרות), או `python קובץ` עם הקובץ במירכאות אם יש רווחים בשם.
    """
    if profile.run_command:
        return profile.run_command
    return f"python {shlex.quote(profile.entrypoint)}" if profile.entrypoint else None
