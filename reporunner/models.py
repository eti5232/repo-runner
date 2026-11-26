"""מודלי הנתונים של הסוכן (Pydantic). הקובץ יגדל בכל אבן דרך."""
from typing import Literal

from pydantic import BaseModel, Field


def checkpoint_serializer():
    """
    1. מקבלת: כלום.
    2. מחזירה: JsonPlusSerializer.
    3. עושה: רושמת את כל מודלי Pydantic שבקובץ כמותרים לטעינה מקובץ השמירה (LangGraph יחסום טיפוסים לא רשומים).
    """
    from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

    registered = [(__name__, name) for name, obj in globals().items()
                  if isinstance(obj, type) and issubclass(obj, BaseModel) and obj is not BaseModel]
    return JsonPlusSerializer(allowed_msgpack_modules=registered)


class CommandResult(BaseModel):
    """התוצאה של פקודה אחת שרצה בקונטיינר."""

    command: str
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool
    duration_sec: float

    @property
    def ok(self) -> bool:
        """
        1. מקבלת: self.
        2. מחזירה: bool.
        3. עושה: True אם הפקודה הסתיימה בקוד יציאה 0 ובלי חריגת זמן.
        """
        return self.exit_code == 0 and not self.timed_out

    @property
    def output(self) -> str:
        """
        1. מקבלת: self.
        2. מחזירה: מחרוזת: stdout ואז stderr.
        3. עושה: מאחדת את שני הערוצים, כי שגיאה יכולה להופיע בכל אחד מהם.
        """
        return "\n".join(part for part in (self.stdout.strip(), self.stderr.strip()) if part)


class ProjectProfile(BaseModel):
    """מה שזוהה על הפרויקט מתוך הקבצים שלו."""

    python_version: str
    deps_file: str | None   # requirements.txt / pyproject.toml / setup.py, או None אם אין
    has_tests: bool
    entrypoint: str | None  # הקובץ שמריצים, למשל main.py
    uses_gui: bool = False  # הפרויקט פותח חלון (tkinter, pygame...) ולכן צריך מסך וירטואלי
    run_command: str | None = None  # פקודת הרצה מפורשת (streamlit run ...), כשלא מספיק `python קובץ`


class Step(BaseModel):
    """צעד אחד בתוכנית ההרצה."""

    command: str
    purpose: str
    in_dockerfile: bool = True  # צעדי בדיקה (כמו python --version) לא נכנסים ל-Dockerfile
    is_fix: bool = False        # צעד שנוסף כתיקון. אם הוא נכשל, מחליפים אותו ולא מנסים שוב
    as_root: bool = False       # רץ כ-root. רק פקודת מערכת (apt) שאדם אישר


class SuccessCheck(BaseModel):
    """איך קובעים שהפרויקט "עובד".

    command: הפקודה מסתיימת בקוד 0.
    run: מריצים את הפרויקט עצמו – הצלחה אם הסתיים בקוד 0 (סקריפט) או אם הוא מאזין ועונה ב-HTTP (שרת).
    """

    command: str
    kind: Literal["command", "run"] = "command"
    timeout: int = 120
    help_only: bool = False  # כלי שורת פקודה שדורש ארגומנטים: אומת ב---help בלבד, ולא הורצה פקודה ממשית


class Diagnosis(BaseModel):
    """תוצאת האבחון. המודל מחזיר אותה כקריאה לכלי, ולכן Pydantic מוודא שהמבנה תקין."""

    category: Literal[
        "missing_package", "version_conflict", "missing_system_library",
        "missing_env_var", "missing_file", "python_version", "code_bug", "other",
    ]
    summary: str     # משפט אחד: מה השתבש
    root_cause: str  # הסיבה הבסיסית, כפי שהתגלתה מהשגיאה ומהקבצים
    env_var_name: str | None = Field(
        default=None,
        description="Only when category is missing_env_var: the exact name of the missing environment variable.",
    )
    python_version: str | None = Field(
        default=None,
        description="Only when category is python_version: the Python version to switch to, one of 3.8, 3.9, 3.10, 3.11, 3.12, 3.13.",
    )


class Fix(BaseModel):
    """תיקון מוצע: פקודות shell שירוצו בתיקיית הפרויקט לפני שהצעד שנכשל ירוץ שוב."""

    commands: list[str]
    explanation: str


class Attempt(BaseModel):
    """ניסיון תיקון אחד. הרשימה שלהם היא ה"זיכרון" של הסוכן."""

    number: int
    failed_command: str
    error: str
    category: str
    fix_commands: list[str]


class Risk(BaseModel):
    """סיבה אחת לכך שפקודת תיקון דורשת אישור אדם."""

    kind: Literal["system", "remote_script", "secret", "code_change", "custom_source", "outside", "unrecognized", "repeated"]
    command: str


class Approval(BaseModel):
    """החלטה של אדם. ה-detail לעולם לא מכיל ערך של סוד – רק שם של משתנה."""

    kind: Literal["secret_needed", "sensitive_fix", "attempts_exhausted"]
    action: str
    detail: str


class Preview(BaseModel):
    """איך המשתמשת רואה את הפרויקט שרץ: דפדפן חי (web/desktop) או הקלטת וידאו (recording)."""

    kind: Literal["web", "desktop", "recording"]
    url: str   # web/desktop: כתובת בדפדפן; recording: נתיב בשרת של הסוכן
    note: str = ""


class Report(BaseModel):
    """התוצר הסופי של ריצה."""

    succeeded: bool
    summary: str
    dockerfile: str
    run_script: str
    python_version: str = "3.12"
    env_vars: list[str] = []      # משתני סביבה שהפרויקט דורש (השמות בלבד, לעולם לא הערכים)
    fixes: list[str] = []         # מה היה שבור ואיך תוקן
    port: int | None = None       # אם הפרויקט שרת – הפורט שבו הוא ענה
    help_only: bool = False       # הפרויקט הוא כלי שורת פקודה שדורש ארגומנטים, ואומת ב---help בלבד
    cli_commands: list[str] = []  # פקודות המשנה שנמצאו ב---help (למשל train, watch)
    cli_help: dict[str, str] = {}  # תיאור קצר לכל פקודת משנה, אם ה---help מציג אותו
    run_command: str = ""         # הפקודה שמריצה את הפרויקט, למשל "python main.py"
