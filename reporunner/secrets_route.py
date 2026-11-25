"""נקודת קצה (endpoint) שכותבת סוד ישירות לקונטיינר, מחוץ לגרף.

הסיבה: הערך של סוד (מפתח API וכדומה) לא יכול לעבור דרך ה-State, כי ה-State נשמר ב-checkpointer ונשלח ל-LangSmith.
ממשק ה-React שולח את הסוד לכאן, הנקודה כותבת אותו לקונטיינר, ורק אחרי זה הממשק מחדש את הגרף עם {"action": "provided"}.

המסלולים נרשמים בשרת של LangGraph דרך reporunner/api.py.
"""
import re

from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from reporunner.sandbox import Sandbox

CONTAINER_NAME = re.compile(r"reporunner-[A-Za-z0-9_.-]+")  # רק קונטיינרים של RepoRunner, לא כל קונטיינר במחשב


def _write_secret(container: str, name: str, value: str) -> None:
    """
    1. מקבלת: container (שם הקונטיינר), name (שם המשתנה), value (הערך).
    2. מחזירה: כלום.
    3. עושה: מתחברת לקונטיינר וכותבת בו את הסוד. פונקציה רגילה (לא async) כי Docker SDK חוסם.
    """
    Sandbox.attach(container).set_secret(name, value)


async def write_secret(request: Request) -> JSONResponse:
    """
    1. מקבלת: בקשת POST עם JSON: {container, name, value}.
    2. מחזירה: {"ok": true}, או שגיאה 400 עם הסבר.
    3. עושה: בודקת את הקלט וכותבת את הסוד לקונטיינר. הערך לא נכתב ללוג ולא מוחזר בתשובה.
    """
    try:
        body = await request.json()
        container, name, value = body["container"], body["name"], body["value"]
    except (ValueError, KeyError, TypeError):
        return JSONResponse({"error": "נדרשים container, name ו-value"}, status_code=400)
    if not isinstance(value, str) or not CONTAINER_NAME.fullmatch(str(container)):
        return JSONResponse({"error": "קלט לא תקין"}, status_code=400)
    try:
        await run_in_threadpool(_write_secret, container, str(name), value)
    except ValueError as error:  # שם משתנה לא תקין
        return JSONResponse({"error": str(error)}, status_code=400)
    except Exception:  # noqa: BLE001 – לא מדליפים פרטים פנימיים (ובטח לא את הערך)
        return JSONResponse({"error": "כתיבת הסוד לקונטיינר נכשלה"}, status_code=500)
    return JSONResponse({"ok": True})


routes = [Route("/reporunner/secret", write_secret, methods=["POST"])]
