"""הגדרות ריצה שאינן חלק מה-State: איזו גרסה של הסוכן רצה.

ב-LangGraph זה נקרא runtime context: מועבר בהפעלת הגרף (graph.invoke(..., context=...)), והצמתים קוראים אותו.
כך אותו קוד מריץ גם את v1 (הבסיס של הניסוי, לא משתנה) וגם את v2 (המשופרת), בלי שני עותקים.
"""
from dataclasses import dataclass
from typing import Literal

AgentVersion = Literal["v1", "v2"]


@dataclass
class RunContext:
    """הגדרות הריצה. ברירת המחדל v1, כדי שניסויים קיימים ימשיכו להתנהג בדיוק כמו קודם."""

    agent_version: AgentVersion = "v1"


def version_of(context: RunContext | None) -> AgentVersion:
    """
    1. מקבלת: context (RunContext, או None אם לא הועבר).
    2. מחזירה: גרסת הסוכן: 'v1' או 'v2'.
    3. עושה: קוראת את הגרסה מההקשר, ומחזירה v1 כשלא הועבר הקשר (כמו בהרצה ישנה או בבדיקות).
    """
    return context.agent_version if context else "v1"
