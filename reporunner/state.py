"""ה-State של הגרף: הזיכרון המשותף שכל הצמתים קוראים ממנו וכותבים אליו.

כל צומת מחזיר dict עם השדות שהוא משנה בלבד, ו-LangGraph ממזג אותם לתוך ה-State.
השדות יתווספו לאורך אבני הדרך (M4: אישורים).
"""
import operator
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

from reporunner.models import (
    Approval, Attempt, CommandResult, Diagnosis, Fix, Preview, ProjectProfile, Report, Risk, Step, SuccessCheck,
)


class RunState(TypedDict, total=False):
    # --- קלט ---
    source: str                       # קישור GitHub או נתיב לתיקייה מקומית
    commit: str | None                # נעילה ל-commit מסוים (לא חובה)
    preview_mode: Literal["none", "live", "recording"]  # מה לעשות בסוף: כלום, תצוגה חיה בדפדפן, או הקלטת וידאו

    # --- הקונטיינר והפרויקט ---
    container: str                    # שם הקונטיינר – לא האובייקט עצמו, כי ה-State חייב להיות ניתן לשמירה
    profile: ProjectProfile
    skipped: list[str]                # מה לא הועתק לקונטיינר (סביבות, git, סודות), להצגה למשתמשת

    # --- התוכנית וההרצה ---
    plan: list[Step]
    step_index: int                   # הצעד הבא להרצה
    success_check: SuccessCheck
    last_result: CommandResult

    # --- אבחון ותיקון ---
    messages: Annotated[list[AnyMessage], add_messages]  # שיחת החקירה של האבחון הנוכחי (מתאפסת אחרי כל תיקון)
    tool_calls_used: int              # כמה קריאות לכלים כבר היו באבחון הנוכחי
    diagnosis: Diagnosis | None
    proposed_fix: Fix | None
    fix_risks: list[Risk]             # סיבות שהתיקון המוצע דורש אישור (ריק = בטוח)
    human_feedback: str | None        # הסיבה שאדם דחה תיקון – נשלחת למודל להצעה חדשה
    decision: str                     # ההחלטה האחרונה של אדם; לפיה הניתוב ממשיך
    approvals: Annotated[list[Approval], operator.add]  # יומן ההחלטות (בלי ערכי סודות)
    attempt_limit: int                # מגבלת הניסיונות. אדם יכול להגדיל אותה
    attempts: int                     # כמה תיקונים כבר נוסו
    attempt_history: Annotated[list[Attempt], operator.add]  # reducer: רשימה שרק מתארכת, לא נדרסת

    # --- בדיקת פקודות ותצוגה ---
    preview_command: str | None       # הפקודה שפותחת חלון (נמצאה בבדיקת הפקודות), לתצוגה חיה או להקלטה
    preview: Preview | None           # התצוגה שהוכנה למשתמשת

    # --- תוצאה ---
    status: Literal["running", "succeeded", "failed"]
    report: Report
