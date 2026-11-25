"""בדיקה לזיהוי שגיאת שימוש של כלי שורת פקודה. הפונקציה טהורה: בלי Docker ובלי מודל.

הרצה:  python -m pytest tests/test_verify.py -v
"""
import pytest

from reporunner.models import CommandResult
from reporunner.nodes import is_usage_error


def _result(exit_code: int, text: str, timed_out: bool = False) -> CommandResult:
    return CommandResult(command="python main.py", exit_code=exit_code, stdout=text, stderr="", timed_out=timed_out, duration_sec=1)


@pytest.mark.parametrize("result, expected", [
    # argparse: מה שקרה בפרויקט האמיתי
    (_result(2, "usage: main.py [-h] {train,watch,learn} ...\nmain.py: error: the following arguments are required: command"), True),
    (_result(2, "Usage: tool [OPTIONS] COMMAND"), True),                  # click / typer
    (_result(2, "Traceback ... something else"), False),                 # קוד 2 בלי usage: לא ניחוש
    (_result(1, "usage: main.py [-h]"), False),                          # קוד 1 הוא שגיאה רגילה
    (_result(2, "usage: main.py", timed_out=True), False),               # חריגת זמן
    (_result(1, "ModuleNotFoundError: No module named 'x'"), False),
])
def test_usage_error_detection(result, expected):
    assert is_usage_error(result) is expected
