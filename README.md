# RepoRunner

סוכן LangGraph שמקבל פרויקט Python, מריץ אותו בקונטיינר Docker מבודד, מאבחן ומתקן שגיאות בלולאה, ועוצר לאישור אדם לפני פעולות רגישות. בסוף הוא מחזיר Dockerfile עובד ודוח תיקונים.

> הקובץ הזה מתעדכן לאורך הפרויקט. התוכנית המלאה: [PLAN.md](PLAN.md)

## דרישות מקדימות

- Python 3.11 ומעלה
- Docker Desktop פועל
- מפתח API של OpenAI ומפתח של LangSmith

## התקנה

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

אחרי ההעתקה, ממלאים את הערכים ב-`.env`.

### עבודה מאחורי NetFree

חיבורי HTTPS עוברים דרך NetFree, ולכן:
- **במחשב המארח** – הספרייה `truststore` גורמת ל-Python להשתמש במאגר התעודות של Windows, שבו מותקנת התעודה של NetFree.
- **בתוך הקונטיינר** – `pip` ו-`git` לא מכירים את התעודה, ונכשלים בשגיאת `CERTIFICATE_VERIFY_FAILED`. הסוכן מייצא את תעודות NetFree מ-Windows ומזריק אותן לכל קונטיינר.

## הרצה

```powershell
python cli.py evaluation/fixtures/ok_requests_script
python cli.py https://github.com/octocat/Hello-World
```

בסוף כל ריצה נשמרים התוצרים ב-`.reporunner/runs/<מזהה הריצה>/`: `Dockerfile`, `run.sh` ו-`REPORT.md`
(מה היה שבור, איך תוקן, ואילו משתני סביבה נדרשים). בנייה והרצה:

```powershell
docker build -t myproject <תיקיית הפרויקט המקורי עם ה-Dockerfile>
```

> ברשת עם מסנן כמו NetFree, גם `docker build` צריך להכיר את התעודה של המסנן (ראו `tests/test_dockerfile.py`).

כשהסוכן צריך החלטה (פעולה רגישה, סוד חסר, או שנגמרו הניסיונות) הוא עוצר וממתין. אפשר לענות מיד, או לסגור את התוכנה
ולהמשיך אחר כך מאותה נקודה (המצב נשמר ב-`.reporunner/checkpoints.sqlite`, והקונטיינר נשאר פעיל):

```powershell
python cli.py --resume --thread <מזהה הריצה שהודפס בהתחלה>
```

לצפייה בגרף חי ב-LangGraph Studio:

```powershell
langgraph dev
```

> הקובץ `.env` חייב להכיל ASCII בלבד (בלי עברית בהערות): הכלי `langgraph dev` קורא אותו בקידוד של Windows העברי ונכשל על UTF-8.

## ממשק React

ממשק אינטרנט מלא (`frontend/`) שמחובר לסוכן האמיתי דרך שרת LangGraph. שני תהליכים במקביל:

```powershell
.\.venv\Scripts\langgraph.exe dev --no-browser --no-reload --allow-blocking
```

```powershell
cd frontend
npm install
npm run dev
```

האתר נפתח ב-http://localhost:5180. מסכים: הבית (הדבקת קישור), כל הריצות, ומסך ריצה חי עם מסלול הסוכן, ציר זמן, כרטיס אישור, פקודות ותוצרים. הסודות נכתבים לקונטיינר דרך `reporunner/secrets_route.py` ולא עוברים בגרף. פירוט המבנה: [frontend/README.md](frontend/README.md).

### תצוגה חיה או הקלטה

במסך ההתחלה בוחרים מה לעשות כשהפרויקט רץ: **רק תוצרים**, **תצוגה חיה בדפדפן**, או **הקלטת וידאו**.

- **פרויקט שרת:** הסוכן מריץ אותו בקונטיינר ופותח לך טאב עם האתר (פורט אקראי פנוי במחשב).
- **פרויקט עם חלון (tkinter, pygame):** הסוכן מריץ אותו על מסך וירטואלי (Xvfb) ומציג אותו בטאב דרך noVNC, או מקליט כמה שניות.
- התצוגה החיה נשארת פעילה עד שלוחצים "עצור תצוגה", ונסגרת לבד אחרי 30 דקות.
- לפני כל זה הסוכן מריץ **בדיקת פקודות**: כל פקודת משנה רצה כמה שניות, כדי לתפוס בעיות שאימות ב---help מפספס (למשל `tkinter` בפקודת `watch`).

## הרחבת דפדפן ל-GitHub

התיקייה `extension/` היא הרחבת Chrome/Edge שמוסיפה בכל דף ריפו ב-github.com כפתור **"הרץ עם RepoRunner"**. לחיצה פותחת את האתר עם הקישור כבר מוזן (`?source=...`). התקנה והסבר: [extension/README.md](extension/README.md).

## בדיקות

מתיקיית הפרויקט (דורש Docker פועל):

```powershell
python -m pytest tests -v
```

## תכנון להמשך (עוד לא ממומש)

### פתיחת Pull Request אוטומטית

כשהפרויקט עובר אימות, כפתור אחד יפתח Pull Request בריפו המקורי עם התוצרים שהסוכן יצר:
`Dockerfile`, `run.sh` ותיקוני `requirements.txt`. תיאור ה-PR נבנה מהדוח (מה היה שבור, מה תוקן, איך אומת), בקוד דטרמיניסטי וללא LLM.

- **אישור אדם:** פתיחת PR היא פעולה כלפי חוץ, ולכן תמתין לאישור מפורש, באותו מנגנון של `human_approval`.
- **הרשאות:** התחברות ל-GitHub, יצירת fork וענף חדש, והעלאת הקבצים דרך ה-API.
- **סודות:** ה-token של GitHub ייכנס מחוץ לגרף (כמו מפתחות API), ולא יישמר ב-State או ב-LangSmith.
- **מועד:** אחרי M7, ביחד עם הממשק המחובר לסוכן.

## עמידה בדרישות התרגיל

| # | דרישה | מצב |
|---|---|---|
| 1 | שימוש ב-`langgraph` | ⏳ |
| 2 | לולאה / ענף מותנה | ⏳ |
| 3 | `interrupt` ו-human-in-the-loop | ⏳ |
| 4 | דאטהסט והערכה ב-LangSmith, לפני ואחרי שיפור | ⏳ |
| 5 | README עם trace ותובנה | ⏳ |
