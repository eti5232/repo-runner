"""שער הבטיחות: מחליט אם פקודת תיקון רצה אוטומטית או דורשת אישור אדם.

העיקרון: **רשימת היתר (allowlist), לא רשימת איסורים.** רק פקודות שמוכרות כבטוחות רצות לבד;
כל דבר אחר – כולל מה שלא הכרנו – עובר לאדם. ההחלטה נקבעת בקוד קבוע, ולא ע"י המודל,
כדי שגם מודל ש"שוכנע" ע"י README זדוני לא יוכל להריץ פקודה רגישה בלי אישור.
"""
import re
import shlex

from reporunner.models import Risk

DEP_FILE = r"requirements[\w.\-]*\.txt"

# --- פקודות שמותרות לרוץ אוטומטית (כל קטע בפקודה חייב להתאים לאחת) ---
ALLOWED = [
    re.compile(r"^(python -m )?pip (install|uninstall -y|uninstall|list|show|freeze)\b"),
    re.compile(r"^python --version$"),
    re.compile(r"^python -m (pytest|compileall)\b"),
    re.compile(rf"^(echo|printf) .+ >>? {DEP_FILE}$"),       # הוספת שורה לקובץ תלויות
    re.compile(rf"^sed -i .+ {DEP_FILE}$"),                  # עריכת קובץ תלויות
]

SYSTEM_TOOLS = {"apt", "apt-get", "sudo", "su", "dpkg", "yum", "apk"}
CUSTOM_SOURCE = re.compile(r"(--index-url|--extra-index-url|--trusted-host|--find-links|://|git\+|\s-[ief]\s|--editable)")
REMOTE_SCRIPT = re.compile(r"(curl|wget)[^|]*\|\s*(sudo\s+)?(ba)?sh")
SECRET_ASSIGN = re.compile(r"\b[A-Z0-9_]*(KEY|TOKEN|SECRET|PASSWORD|PASSWD)[A-Z0-9_]*=", re.IGNORECASE)
SEGMENT_SPLIT = re.compile(r"&&|\|\||;|\||\n")


def _classify_segment(segment: str) -> str | None:
    """
    1. מקבלת: segment: חלק אחד מפקודה (בלי && או ;).
    2. מחזירה: None אם בטוח, אחרת סוג הסיכון.
    3. עושה: בודקת לפי כללים קבועים: מערכת, סוד, מקור התקנה מותאם, שינוי קוד, נתיב מחוץ לפרויקט. מה שלא ברשימת ההיתר נחשב לא מוכר.
    """
    try:
        tokens = shlex.split(segment)
    except ValueError:
        return "unrecognized"  # מרכאות לא מאוזנות – לא ניתן לנתח, לכן לא סומכים
    if not tokens:
        return None
    if tokens[0] in SYSTEM_TOOLS:
        return "system"
    if SECRET_ASSIGN.search(segment):
        return "secret"
    is_pip = bool(re.match(r"^(python -m )?pip (install|uninstall)", segment))
    if is_pip and CUSTOM_SOURCE.search(f" {segment}"):
        return "custom_source"
    if any(p.match(segment) for p in ALLOWED):
        return None
    if re.search(r"\.py\b", segment):
        return "code_change"
    if any(t.startswith(("/", "~")) and not t.startswith("/workspace") or ".." in t.split("/") for t in tokens[1:]):
        return "outside"
    return "unrecognized"


def assess(commands: list[str]) -> list[Risk]:
    """
    1. מקבלת: commands: רשימת פקודות התיקון המוצעות.
    2. מחזירה: רשימת Risk. ריקה אומרת שהכול בטוח.
    3. עושה: מפרקת כל פקודה לחלקים ומסווגת כל חלק. היתר-בלבד: מה שלא הוכר כבטוח עובר לאדם.
    """
    risks: list[Risk] = []
    for command in commands:
        if REMOTE_SCRIPT.search(command):
            risks.append(Risk(kind="remote_script", command=command))
        elif "<<" in command or re.search(r"\bpython3?\s+(-c\b|-(\s|$))", command):
            # קוד פייתון שנכתב "בתוך" הפקודה: לא ניתן לבדוק מה הוא עושה
            risks.append(Risk(kind="code_change", command=command))
        else:
            for segment in filter(None, (s.strip() for s in SEGMENT_SPLIT.split(command))):
                kind = _classify_segment(segment)
                if kind:
                    risks.append(Risk(kind=kind, command=segment))
    return risks
