"""ביטול ריצה: מחיקת הקונטיינרים שלה.

למה: ביטול בשרת לא עוצר פעולה שכבר רצה (כמו git clone), ודוח (report), שמוחק את הקונטיינר, כבר לא ירוץ.
לכן כל קונטיינר מסומן במזהה הריצה, ובעצירה מוחקים לפי הסימון. ריצה שעוד באמצע השכפול בודקת בסופו אם בוטלה.
"""
import docker

THREAD_LABEL = "reporunner.thread"

_cancelled: set[str] = set()  # הגרף ונקודות הקצה רצים באותו תהליך של שרת LangGraph


def current_thread_id() -> str | None:
    """
    1. מקבלת: כלום.
    2. מחזירה: מזהה הריצה (thread) הנוכחית, או None כשלא רצים בתוך גרף (למשל בבדיקות).
    3. עושה: קוראת את המזהה מההגדרות ש-LangGraph מחזיק בזמן ריצת צומת.
    """
    from langgraph.config import get_config

    try:
        return get_config().get("configurable", {}).get("thread_id")
    except RuntimeError:
        return None


def is_cancelled(thread_id: str | None) -> bool:
    """
    1. מקבלת: thread_id.
    2. מחזירה: bool.
    3. עושה: True אם המשתמשת עצרה את הריצה הזו.
    """
    return thread_id in _cancelled


def cancel(thread_id: str) -> int:
    """
    1. מקבלת: thread_id.
    2. מחזירה: כמה קונטיינרים נמחקו.
    3. עושה: מסמנת שהריצה בוטלה ומוחקת את הקונטיינרים שלה.
    """
    _cancelled.add(thread_id)
    removed = 0
    for container in docker.from_env().containers.list(all=True, filters={"label": f"{THREAD_LABEL}={thread_id}"}):
        try:
            container.remove(force=True)
            removed += 1
        except docker.errors.NotFound:
            pass
    return removed
