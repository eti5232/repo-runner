"""בדיקת הקלט של הריצה (קישור או תיקייה) לפני שמתחילים, והודעות שגיאה ברורות בעברית.

בלי זה, קלט שגוי נראה כמו ריצה "תקועה": הסוכן ניסה לשכפל משהו שאינו ריפו, או חיכה לחלון התחברות של Git.
"""
from pathlib import Path

URL_PREFIXES = ("https://", "http://", "git@", "ssh://")


class SourceError(RuntimeError):
    """הפרויקט לא ניתן להבאה. ההודעה כתובה למשתמשת ומוצגת באתר כמו שהיא."""


def normalize_source(text: str) -> str:
    """
    1. מקבלת: text (מה שהמשתמשת הדביקה).
    2. מחזירה: הקלט בלי רווחים מסביב ובלי מירכאות.
    3. עושה: מנקה את מה ש-Windows מוסיף ב"העתק כנתיב" (מירכאות מסביב לנתיב).
    """
    return text.strip().strip("\"'").strip()


def source_problem(source: str) -> str | None:
    """
    1. מקבלת: source (קלט נקי).
    2. מחזירה: הסבר בעברית מה לא בסדר ומה לעשות, או None אם הקלט תקין.
    3. עושה: מבדילה בין תיקייה, קובץ, קישור, ונתיב שלא קיים.
    """
    if not source:
        return "לא הוזן קישור או תיקייה."
    if source.startswith(URL_PREFIXES):
        return None
    path = Path(source)
    if path.is_dir():
        return None
    if path.is_file():
        return f"נתת קובץ ולא תיקייה. הדביקי את התיקייה שלו: {path.parent}"
    return f"לא נמצאה תיקייה כזו, וזה גם לא קישור לריפו: {source}"


def clone_problem(stderr: str) -> str:
    """
    1. מקבלת: stderr (פלט השגיאה של git clone).
    2. מחזירה: הסבר בעברית.
    3. עושה: מתרגמת את הכשלים הנפוצים (ריפו לא קיים או פרטי, אין רשת) להודעה שאפשר לפעול לפיה.
    """
    text = stderr.lower()
    if any(mark in text for mark in ("not found", "authentication", "could not read username", "permission denied", "403")):
        return "הריפו לא נמצא, או שהוא פרטי ואין הרשאה. בדקי את הקישור, או הורידי את הפרויקט ותני תיקייה."
    if any(mark in text for mark in ("could not resolve", "unable to access", "timed out", "ssl", "certificate")):
        return "אין חיבור לריפו. בדקי את החיבור לאינטרנט ואת NetFree, ונסי שוב."
    last = (stderr.strip().splitlines() or ["סיבה לא ידועה"])[-1]
    return f"שכפול הפרויקט נכשל: {last[:200]}"
