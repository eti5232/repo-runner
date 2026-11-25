"""קיצור פלט של פקודות לפני שהוא נשלח למודל.

פלט ארוך מבזבז טוקנים, אבל קיצור נאיבי (התחלה וסוף) יכול להחמיץ את השגיאה האמיתית כשהיא באמצע.
לכן כאן שומרים תמיד את ה-traceback האחרון, ורק את האמצע הלא-רלוונטי מוחקים.
"""

TRACEBACK_MARK = "Traceback (most recent call last)"


def _omitted(count: int) -> str:
    """
    1. מקבלת: count (כמה תווים הושמטו).
    2. מחזירה: שורת סימון.
    3. עושה: בונה את השורה שמסמנת בטקסט מקוצר שחלק נמחק.
    """
    return f"\n... [{count} תווים הושמטו] ...\n"


def clip_output(text: str, limit: int) -> str:
    """
    1. מקבלת: text (פלט פקודה) ו-limit (כמה תווים לכל היותר לשמור, בערך).
    2. מחזירה: הטקסט כמו שהוא אם הוא קצר מספיק; אחרת גרסה מקוצרת.
    3. עושה: מקצרת תוך שמירת ה-traceback האחרון: אם יש כזה באמצע הפלט, נשמרים תחילת הפלט, ה-traceback
       (ההתחלה שלו והשורות האחרונות שלו, שבהן הודעת השגיאה) וסוף הפלט. בלי traceback: תחילה וסוף בלבד.
    """
    if len(text) <= limit:
        return text

    head_size = limit // 4
    traceback_start = text.rfind(TRACEBACK_MARK)

    if traceback_start >= head_size:
        room = limit - head_size  # מה שנשאר אחרי ההתחלה
        head = text[:head_size] + _omitted(traceback_start - head_size)
        rest = text[traceback_start:]
        if len(rest) <= room:
            return head + rest  # ה-traceback וכל מה שאחריו נכנסים בשלמותם
        half = room // 2
        return head + rest[:half] + _omitted(len(rest) - room) + rest[-half:]

    half = limit // 2
    return text[:half] + _omitted(len(text) - limit) + text[-half:]
