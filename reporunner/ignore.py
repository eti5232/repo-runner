"""מה לא מעתיקים לקונטיינר כשהפרויקט מגיע מתיקייה במחשב.

למה: סביבות וירטואליות, היסטוריית git ומטמונים כבדים (מאות מגה-בייט) ולא שייכים לקונטיינר, שבונה סביבה משלו.
וגם מפתחות וסודות (.env, מפתחות פרטיים) לא אמורים להגיע לקוד שרץ בקונטיינר: אם הפרויקט צריך מפתח,
הסוכן מבקש אותו ממך ושומר אותו בקונטיינר בלבד.
"""

# תיקיות שמדלגים עליהן לגמרי
SKIP_DIR_NAMES = frozenset({
    ".venv", "venv", "__pycache__", ".git", ".idea", ".vscode", "node_modules",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox", ".reporunner",
})

# קבצי סודות
SECRET_FILE_NAMES = frozenset({"id_rsa", "id_ed25519", ".netrc"})
SECRET_SUFFIXES = (".pem", ".key")
ENV_TEMPLATE_SUFFIXES = (".example", ".sample", ".template", ".dist")  # דוגמאות בלי ערכים אמיתיים: כן מעתיקים


def _is_secret_file(name: str) -> bool:
    """
    1. מקבלת: name (שם קובץ, בלי נתיב).
    2. מחזירה: bool.
    3. עושה: True אם זה קובץ סודות: .env וגרסאותיו (חוץ מקבצי דוגמה), מפתחות פרטיים ותעודות.
    """
    lowered = name.lower()
    if lowered == ".env" or lowered.startswith(".env."):
        return not lowered.endswith(ENV_TEMPLATE_SUFFIXES)
    return lowered in SECRET_FILE_NAMES or lowered.endswith(SECRET_SUFFIXES)


def skip_label(name: str, is_dir: bool) -> str | None:
    """
    1. מקבלת: name (שם הקובץ או התיקייה, בלי נתיב) ו-is_dir.
    2. מחזירה: שם להצגה אם מדלגים עליו, אחרת None.
    3. עושה: מחליטה אם לא להעתיק: תיקיות כבדות או מיותרות, וקבצי סודות.
    """
    if is_dir:
        return name if name in SKIP_DIR_NAMES else None
    return name if _is_secret_file(name) else None
