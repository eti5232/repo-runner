"""נקודות קצה לתצוגה ולעצירה: הגשת קובץ ההקלטה לדפדפן, עצירת תצוגה חיה, ומחיקת הקונטיינרים של ריצה שנעצרה.

מתווספות לשרת של LangGraph דרך reporunner/api.py.
"""
import re

from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.routing import Route

from reporunner import cancel, display
from reporunner.sandbox import Sandbox

CONTAINER_NAME = re.compile(r"reporunner-[A-Za-z0-9_.-]+")  # רק קונטיינרים של RepoRunner


async def serve_recording(request: Request) -> Response:
    """
    1. מקבלת: בקשת GET עם container בנתיב.
    2. מחזירה: קובץ הווידאו (mp4), או 404.
    3. עושה: מגישה לדפדפן את ההקלטה ששמרה הריצה.
    """
    name = request.path_params["container"]
    if not CONTAINER_NAME.fullmatch(name):
        return JSONResponse({"error": "שם לא תקין"}, status_code=400)
    path = display.recording_path(name)
    if not path.exists():
        return JSONResponse({"error": "אין הקלטה"}, status_code=404)
    return FileResponse(path, media_type="video/mp4")


def _stop_container(name: str) -> None:
    """
    1. מקבלת: name (שם קונטיינר).
    2. מחזירה: כלום.
    3. עושה: עוצרת ומוחקת את הקונטיינר. פונקציה רגילה כי Docker SDK חוסם.
    """
    Sandbox.attach(name).stop()


async def stop_preview(request: Request) -> JSONResponse:
    """
    1. מקבלת: בקשת POST עם JSON: {container}.
    2. מחזירה: {"ok": true}, או שגיאה 400.
    3. עושה: סוגרת קונטיינר שמריץ תצוגה חיה, כשהמשתמשת לוחצת "עצור".
    """
    try:
        name = (await request.json())["container"]
    except (ValueError, KeyError, TypeError):
        return JSONResponse({"error": "נדרש container"}, status_code=400)
    if not CONTAINER_NAME.fullmatch(str(name)):
        return JSONResponse({"error": "שם לא תקין"}, status_code=400)
    try:
        await run_in_threadpool(_stop_container, name)
    except Exception:  # noqa: BLE001 – הקונטיינר כבר נסגר או לא קיים
        pass
    return JSONResponse({"ok": True})


async def cancel_run(request: Request) -> JSONResponse:
    """
    1. מקבלת: בקשת POST עם JSON: {thread_id}.
    2. מחזירה: {"removed": n}, או שגיאה 400.
    3. עושה: מוחקת את הקונטיינרים של ריצה שהמשתמשת עצרה, כדי שלא יישארו פעילים ברקע.
    """
    try:
        thread_id = str((await request.json())["thread_id"])
    except (ValueError, KeyError, TypeError):
        return JSONResponse({"error": "נדרש thread_id"}, status_code=400)
    if not re.fullmatch(r"[A-Za-z0-9-]{8,64}", thread_id):
        return JSONResponse({"error": "מזהה לא תקין"}, status_code=400)
    return JSONResponse({"removed": await run_in_threadpool(cancel.cancel, thread_id)})


routes = [
    Route("/reporunner/cancel", cancel_run, methods=["POST"]),
    Route("/reporunner/recording/{container}", serve_recording, methods=["GET"]),
    Route("/reporunner/stop", stop_preview, methods=["POST"]),
]
