"""הזיכרון של הסוכן בגרסה v2: מה כבר נוסה, ואיך לא לחזור על זה.

ב-v1 המודל מקבל רק את השגיאה האחרונה, ולכן יכול להציע שוב תיקון שכבר נכשל.
ב-v2 הוא מקבל גם את ההיסטוריה, והקוד (לא המודל) מזהה הצעה שחוזרת על עצמה.
"""
from reporunner.models import Attempt

HISTORY_LIMIT = 5        # כמה ניסיונות אחרונים נשלחים למודל (יותר מזה מבזבז טוקנים)
ERROR_TAIL_CHARS = 200   # כמה מסוף כל שגיאה ישנה נשלח


def normalize(commands: list[str]) -> tuple[str, ...]:
    """
    1. מקבלת: commands (פקודות תיקון).
    2. מחזירה: tuple להשוואה.
    3. עושה: מאחדת רווחים בכל פקודה, כך שהבדל של רווח או ירידת שורה לא נחשב תיקון חדש.
    """
    return tuple(" ".join(command.split()) for command in commands if command.strip())


def is_repeat(commands: list[str], history: list[Attempt]) -> bool:
    """
    1. מקבלת: commands (תיקון מוצע) ו-history (ניסיונות קודמים).
    2. מחזירה: bool.
    3. עושה: True אם אותה רשימת פקודות בדיוק כבר נוסתה בריצה הזו.
    """
    proposed = normalize(commands)
    return bool(proposed) and any(normalize(attempt.fix_commands) == proposed for attempt in history)


def history_text(history: list[Attempt]) -> str:
    """
    1. מקבלת: history (ניסיונות קודמים).
    2. מחזירה: טקסט להוספה לפרומפט, או מחרוזת ריקה אם אין היסטוריה.
    3. עושה: מתארת את הניסיונות האחרונים: מה נכשל ומה נוסה. השגיאות בתוך <error_output>, כי הן נתונים ולא הוראות.
    """
    if not history:
        return ""
    lines = ["", "", "Previous fix attempts in this run. They did not solve the problem, so do not repeat them:"]
    for attempt in history[-HISTORY_LIMIT:]:
        lines += [
            f"Attempt {attempt.number}: failed command: {attempt.failed_command}",
            f"<error_output>\n{attempt.error[-ERROR_TAIL_CHARS:]}\n</error_output>",
            f"Fix tried: {' && '.join(attempt.fix_commands)}",
        ]
    return "\n".join(lines)


def repeat_message(commands: list[str]) -> str:
    """
    1. מקבלת: commands (ההצעה שחזרה על עצמה).
    2. מחזירה: טקסט למודל.
    3. עושה: מסבירה למודל שההצעה נחסמה ומבקשת פתרון אחר.
    """
    return (
        f"Your proposal was BLOCKED: these exact commands were already tried and did not solve the problem: "
        f"{' && '.join(commands)}\nPropose a different fix."
    )
