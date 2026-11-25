"""האפליקציה הנוספת של השרת: מרכזת את כל נקודות הקצה שלנו.

השרת של LangGraph טוען אותה דרך "http" ב-langgraph.json, ומוסיף אותה לצד ה-API הרגיל שלו.
"""
from starlette.applications import Starlette

from reporunner import preview_routes, secrets_route

app = Starlette(routes=[*secrets_route.routes, *preview_routes.routes])
