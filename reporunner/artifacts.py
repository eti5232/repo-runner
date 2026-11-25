"""בניית התוצרים של הריצה: Dockerfile, סקריפט הרצה, ודוח התיקונים.

כל הפונקציות כאן טהורות (מקבלות State ומחזירות טקסט), ולכן בודקים אותן בלי Docker.
החלקים התלויים בשפה (Python) מרוכזים כאן ובמקומות מוגדרים, כדי שאפשר יהיה להוסיף שפה נוספת בקלות.
"""
import json
import re
import shlex

from reporunner import entrypoint
from reporunner.models import ProjectProfile, Report, SuccessCheck
from reporunner.state import RunState

SERVER_PORT = re.compile(r"SERVER_OK port (\d+)")


def run_command(profile: ProjectProfile, check: SuccessCheck) -> str:
    """
    1. מקבלת: profile (ProjectProfile) ו-check (SuccessCheck).
    2. מחזירה: מחרוזת: הפקודה שמריצה את הפרויקט.
    3. עושה: בוחרת את נקודת הכניסה (python main.py); אם אין, pytest כשיש בדיקות; אחרת את פקודת בדיקת ההצלחה.
    """
    command = entrypoint.run_command_of(profile)
    if command:
        return command
    if profile.has_tests:
        return "python -m pytest -q"
    return check.command


def parse_cli_help(help_text: str) -> dict[str, str]:
    """
    1. מקבלת: help_text: הפלט של python main.py --help.
    2. מחזירה: מילון {שם פקודת משנה: תיאור}. ריק אם אין פקודות משנה.
    3. עושה: מוצאת את שורת {train,watch,...} ואת התיאור של כל פקודה, כולל תיאור ש-argparse שבר לשתי שורות.
    """
    found = re.search(r"\{([\w,\-]+)\}", help_text)
    if not found:
        return {}
    commands = {name: "" for name in found.group(1).split(",")}
    current = None
    for line in help_text.splitlines():
        match = re.match(r"^\s{2,}([\w\-]+)\s{2,}(\S.*)$", line)
        if match and match.group(1) in commands:
            current = match.group(1)
            commands[current] = match.group(2).strip()
        elif current and re.match(r"^\s{12,}\S", line):  # שורת המשך: תיאור ארוך ש-argparse שבר לשורה נוספת
            commands[current] += " " + line.strip()
        else:
            current = None
    return commands


def _run_line(command: str) -> str:
    """
    1. מקבלת: command: פקודת shell אחת, אולי מרובת שורות.
    2. מחזירה: שורת RUN תקינה ל-Dockerfile.
    3. עושה: משאירה heredoc כמו שהוא (דורש BuildKit); פקודה מרובת שורות אחרת מחוברת ב-&&.
    """
    if "<<" in command:
        return f"RUN {command}"
    lines = [line.strip() for line in command.splitlines() if line.strip()]
    return "RUN " + " && \\\n    ".join(lines)


def build_dockerfile(profile: ProjectProfile, steps: list[str], run: str, env_vars: list[str],
                     port: int | None, succeeded: bool, help_only: bool = False) -> str:
    """
    1. מקבלת: profile, steps (פקודות ההתקנה), run, env_vars, port, succeeded, help_only.
    2. מחזירה: טקסט ה-Dockerfile.
    3. עושה: בונה FROM, WORKDIR, COPY, שורת RUN לכל צעד, EXPOSE ו-CMD. בכלי שורת פקודה: ENTRYPOINT ו-CMD [--help].
    הערה: שמות של סודות מופיעים רק כהערה, אף פעם לא הערכים.
    """
    lines = ["# syntax=docker/dockerfile:1"]  # מאפשר heredoc ב-RUN (BuildKit)
    if not succeeded:
        lines += ["# WARNING: RepoRunner did not manage to run this project. The steps below are only the ones that worked."]
    lines += [f"FROM python:{profile.python_version}-slim", "WORKDIR /app", "COPY . ."]
    lines += [_run_line(step) for step in steps]
    for name in env_vars:  # סודות לא נכנסים ל-Dockerfile: רק מציינים שהם נדרשים בהרצה
        lines.append(f"# Required at runtime: docker run -e {name}=<value> ...")
    if port:
        lines.append(f"EXPOSE {port}")
    if help_only:
        # כלי שורת פקודה: ה-ENTRYPOINT הוא הפקודה, וה-CMD ברירת מחדל שאפשר להחליף: docker run <image> train
        lines += [f"ENTRYPOINT {json.dumps(shlex.split(run))}", 'CMD ["--help"]']
    else:
        lines.append(f"CMD {json.dumps(['sh', '-c', run])}")  # JSON תקין = הצורה המומלצת ל-CMD
    return "\n".join(lines) + "\n"


def build_run_script(steps: list[str], run: str) -> str:
    """
    1. מקבלת: steps (פקודות ההתקנה) ו-run (פקודת ההרצה).
    2. מחזירה: טקסט של סקריפט sh.
    3. עושה: יוצרת סביבה וירטואלית, מריצה את צעדי ההתקנה ואחריהם את פקודת ההרצה.
    """
    return "\n".join(["#!/bin/sh", "set -e", "python -m venv .venv", ". .venv/bin/activate", *steps, run]) + "\n"


def build_fixes(state: RunState) -> list[str]:
    """
    1. מקבלת: state: ה-State של הריצה.
    2. מחזירה: רשימת שורות: מה נכשל ואיך תוקן.
    3. עושה: מרכזת את attempt_history, ומוסיפה סודות שהמשתמש סיפק (השם בלבד) כדי שהספירה תתאים ל-attempts.
    """
    lines = [
        f"{a.number}. [{a.category}] נכשל: {a.failed_command} | תיקון: {'; '.join(c.splitlines()[0] for c in a.fix_commands)}"
        for a in state.get("attempt_history", [])
    ]
    # סוד שאדם סיפק נספר כניסיון (attempts), אבל לא נרשם ב-attempt_history. מוסיפים אותו כדי שהספירות יתאימו
    secrets = [a for a in state.get("approvals", []) if a.kind == "secret_needed" and a.action == "provided"]
    return lines + [f"{len(lines) + i}. [missing_env_var] סופק המשתנה {a.detail} (הערך אינו נשמר)"
                    for i, a in enumerate(secrets, start=1)]


def build_report(state: RunState) -> Report:
    """
    1. מקבלת: state: ה-State הסופי של הריצה.
    2. מחזירה: Report: סיכום, Dockerfile, סקריפט, פורט, משתני סביבה ופקודות CLI.
    3. עושה: קובעת אם הפרויקט רץ, אוספת את הצעדים שהצליחו, לומדת פורט ופקודות מהפלט, וכותבת את הסיכום והתוצרים.
    """
    succeeded = state.get("status") == "succeeded"
    profile, check = state["profile"], state["success_check"]
    steps = [s.command for s in state["plan"][: state["step_index"]] if s.in_dockerfile]
    run = run_command(profile, check)

    env_vars = [a.detail for a in state.get("approvals", []) if a.kind == "secret_needed" and a.action == "provided"]
    match = SERVER_PORT.search(state["last_result"].stdout) if succeeded else None
    port = int(match.group(1)) if match else None

    help_only = succeeded and check.help_only
    cli = parse_cli_help(state["last_result"].output) if help_only else {}

    attempts = state.get("attempts", 0)
    if help_only:
        summary = (f"הפרויקט הוא כלי שורת פקודה שדורש פקודת משנה, והוא תקין: הייבואים והפרסור עובדים (Python {profile.python_version}). "
                   f"אומת ב---help בלבד, ולא הורצה פקודה ממשית.")
    elif succeeded:
        summary = f"הפרויקט רץ (Python {profile.python_version}) אחרי {attempts} תיקונים. בדיקת ההצלחה: {check.command}"
    else:
        failed = state["last_result"]
        summary = (f"הפרויקט לא רץ אחרי {attempts} ניסיונות תיקון. "
                   f"הפקודה שנכשלה: {failed.command} (קוד יציאה {failed.exit_code})")

    return Report(
        succeeded=succeeded, summary=summary, python_version=profile.python_version,
        dockerfile=build_dockerfile(profile, steps, run, env_vars, port, succeeded, help_only),
        run_script=build_run_script(steps, check.command if help_only else run), env_vars=env_vars,
        fixes=build_fixes(state), port=port, help_only=help_only, cli_commands=list(cli), cli_help=cli,
        run_command=run,
    )


def render_markdown(report: Report, source: str) -> str:
    """
    1. מקבלת: report ו-source (מקור הפרויקט).
    2. מחזירה: טקסט Markdown.
    3. עושה: מרכיבה דוח קריא: תוצאה, מה תוקן, משתני סביבה, פקודות הרצה ב-Docker ופקודות ה-CLI שנמצאו.
    """
    lines = [f"# דוח RepoRunner", "", f"**פרויקט:** {source}", f"**תוצאה:** {'✔ רץ' if report.succeeded else '✘ לא רץ'}",
             f"**גרסת Python:** {report.python_version}", "", report.summary, ""]
    if report.fixes:
        lines += ["## מה היה שבור ואיך תוקן", *report.fixes, ""]
    if report.env_vars:
        lines += ["## משתני סביבה נדרשים", *[f"- `{name}`" for name in report.env_vars], ""]
    # בכלי שורת פקודה מוסיפים אחרי שם ה-image את פקודת המשנה (ה---help הוא ברירת המחדל)
    tail = (f" {report.cli_commands[0]}" if report.cli_commands else " <command>") if report.help_only else ""
    lines += ["## הרצה עם Docker", "```", "docker build -t myproject .",
              "docker run --rm " + "".join(f"-e {n}=<value> " for n in report.env_vars) +
              (f"-p {report.port}:{report.port} " if report.port else "") + "myproject" + tail, "```"]
    if report.help_only:
        lines += ["", "## פקודות שנמצאו",
                  *[f"- `{report.run_command} {name}`" + (f" - {text}" if text else "") for name, text in report.cli_help.items()],
                  "", "הרצת פקודה ממשית (למשל אימון) לא נבדקה. פקודה שפותחת חלון (כמו watch) כדאי להריץ במחשב שלך ולא ב-Docker."]
    return "\n".join(lines) + "\n"
