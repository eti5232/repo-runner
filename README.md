# RepoRunner

סוכן LangGraph שמקבל פרויקט Python (קישור GitHub או תיקייה), מריץ אותו בקונטיינר Docker מבודד, מאבחן ומתקן שגיאות בלולאה, ועוצר לאישור אדם לפני פעולות רגישות. בסוף הוא מחזיר Dockerfile, סקריפט הרצה ודוח תיקונים, ואם מבקשים, גם תצוגה חיה או הקלטה של הפרויקט.

**הבעיה:** פרויקט שעובד אצל מי שכתב אותו לא תמיד רץ אצל אחרים: חבילה חסרה, גרסה שלא קיימת, ספריית מערכת, משתנה סביבה. התיקון דורש ניסוי וטעייה, וזה בדיוק מה שהסוכן עושה.

## תוצאות: לפני ואחרי

26 פרויקטים עם תוצאה ידועה מראש, 3 חזרות לכל אחד (78 ריצות בכל גרסה), אותו מודל (`gpt-5.4-mini`).

| מדד | v1 (בסיס) | v2 (משופרת) |
|---|---|---|
| הצלחה | 0.896 | **1.000** |
| עצירה נכונה (עצר רק כשצריך) | 0.897 | **1.000** |
| עמידות להזרקת פרומפט (ראו הסייג למטה) | 1.000 | 1.000 |
| ללא חזרה על תיקון | 1.000 | 1.000 |
| ניסיונות תיקון בממוצע | 0.77 | 0.77 |
| טוקנים לריצה | 1,604 | 1,835 |
| שניות לריצה | 25 | 31 |

הניסויים ב-LangSmith: `reporunner-v1-d1d71a1a` ו-`reporunner-v2-338f7c60`.

### התובנה

> **כל הכישלונות של v1 נבעו מצורת הכתיבה של התיקון, לא מהאבחון.** המודל אבחן נכון ותיקן נכון, אבל ערך את `requirements.txt` בסקריפט Python בכמה שורות. שער הבטיחות לא יכול לדעת מה סקריפט כזה עושה, ולכן סיווג אותו כשינוי קוד ועצר לאישור שלא נדרש. הנחיה אחת, "כתוב פקודה קצרה בשורה אחת", העלתה את ההצלחה מ-0.90 ל-1.0.

שלוש הדוגמאות שהשתנו (כל השאר 3/3 בשתי הגרסאות):

| דוגמה | v1 | v2 |
|---|---|---|
| `broken_conflicting_pins` | 0/3 | 3/3 |
| `broken_impossible_pin` | 0/3 | 3/3 |
| `broken_requirements_typo` | 1/3 | 3/3 |

**מה שלמדנו על בטיחות מול נוחות:** שער בטיחות שמרני עושה את עבודתו, אבל כדי שלא יעצור לשווא, הסוכן צריך לכתוב פעולות שהשער יכול להבין. הפתרון לא היה להחליש את השער.

**מה הניסוי לא מוכיח:**
- ל-v2 נוספו גם זיכרון ניסיונות וחסימת תיקון חוזר. הכישלונות של v1 קרו כבר בניסיון הראשון, ולכן הניסוי **לא מראה** שהתוספות האלה עוזרות.
- **מדד ההזרקה חלש יותר ממה שהמספר נראה.** הוא ממוצע על כל הריצות, ורובן בלי טקסט זדוני. יש שתי דוגמאות הזרקה, ומבדיקת ה-traces המודל ראה את הטקסט הזדוני רק באחת (`injection_error_message`, בתוך הודעת שגיאה) ולא ציית לו, 3 מתוך 3 בכל גרסה. ב-`injection_readme` הוא לא קרא את ה-README, ולכן היא לא בודקת את המודל. ההגנה העיקרית היא שער הבטיחות: בבדיקה נפרדת הוא עוצר את הפקודות הזדוניות משתי הדוגמאות לאישור אדם.
- 1.0 הוא על 26 פרויקטים קטנים שנכתבו בשביל הפרויקט, ו-v2 תוכנן לפי הכישלונות באותו דאטהסט. זה לא אומר שהסוכן יצליח על כל פרויקט.
- v2 צורך כ-14% יותר טוקנים ואיטי בכ-23%.

### Traces

טבלת ההשוואה ב-LangSmith:

![השוואת הניסויים](docs/images/experiment-compare.png)

מדד ההצלחה (`success`), מ-0.90 ל-1.00:

![מדד ההצלחה](docs/images/experiment-success.png)

אותה דוגמה (`broken_requirements_typo`) ב-v1, שנעצרת לאישור מיותר:

![trace של v1](docs/images/trace-v1.png)

וב-v2, שעוברת בלי עצירה:

![trace של v2](docs/images/trace-v2.png)

## איך זה עובד

### הגרף

```mermaid
graph TD
  START([START]) --> clone_repo --> analyze_project --> plan_run --> execute_step
  execute_step -->|עוד צעדים| execute_step
  execute_step -->|כל הצעדים עברו| verify
  execute_step -->|נכשל| diagnose_error
  diagnose_error -->|צריך לקרוא קבצים| investigate --> diagnose_error
  diagnose_error --> propose_fix --> safety_gate
  diagnose_error -->|גרסת Python| switch_python --> execute_step
  diagnose_error -->|חסר סוד| human_approval
  safety_gate -->|בטוח| apply_fix
  safety_gate -->|רגיש| human_approval
  human_approval -->|אושר| apply_fix
  human_approval -->|נדחה| propose_fix
  human_approval -->|סוד סופק| execute_step
  human_approval -->|עוד ניסיונות| diagnose_error
  human_approval -->|עצור| report
  apply_fix --> execute_step
  apply_fix --> verify
  verify -->|לא עובד| diagnose_error
  verify -->|פקודות משנה או חלון| smoke_test
  verify -->|עובד| report
  verify -->|עובד, ונבחרה תצוגה| open_preview
  smoke_test -->|נשבר| diagnose_error
  smoke_test --> open_preview --> report
  smoke_test --> report
  report --> END([END])
```

בתרשים לא מופיעות קשתות ההגעה למגבלת הניסיונות: מ-`execute_step`, `verify` ו-`smoke_test` אפשר להגיע גם ל-`human_approval`.

**הלולאות:**
1. **צעדים:** `execute_step` חוזר לעצמו עד שהתוכנית נגמרת.
2. **חקירה (ReAct):** `diagnose_error` ↔ `investigate`, עד 5 קריאות לכלי קריאה.
3. **תיקון:** הרצה ← אבחון ← תיקון ← שער בטיחות ← הרצה, עד 8 ניסיונות.
4. **אימות:** `verify` או `smoke_test` שנכשלים מחזירים לאבחון.

### מושגי LangGraph בפרויקט

| מושג | איפה |
|---|---|
| State | `reporunner/state.py` (`RunState`), עם מודלי Pydantic מ-`models.py` |
| Nodes ו-conditional edges | `reporunner/nodes.py`, `nodes_preview.py`, `graph.py` |
| `interrupt` ו-`Command(resume=...)` | `human_approval` |
| Checkpointer | `SqliteSaver` ב-CLI, ושמירת המצב של שרת LangGraph |
| Tools ו-`ToolNode` | `reporunner/tools.py` |
| Runtime context | `reporunner/context.py`: בחירת v1 או v2 באותו קוד |

### איפה משתמשים במודל

**LLM רק איפה שצריך שיפוט:** `diagnose_error` ו-`propose_fix`. כל השאר, כולל ההחלטה אם פקודה בטוחה ואם הפרויקט עובד, הוא קוד דטרמיניסטי. "עובד" נקבע בהרצה אמיתית: סקריפט שהסתיים בקוד 0, שרת שעונה ב-HTTP, או חלון שנפתח.

### מה ב-v2

- פקודות תיקון קצרות בשורה אחת (`sed -i`, `echo >>`), בלי heredoc.
- המודל מקבל את הניסיונות הקודמים, ותיקון שחוזר על עצמו נחסם. אם הוא עדיין חוזר, עובר לאישור אדם.
- אבחון והסבר תיקון בעברית פשוטה.

v1 היא ברירת המחדל ולא השתנתה. הממשק מפעיל v2.

## בטיחות

- קוד הפרויקט רץ רק בקונטיינר: משתמש רגיל (root רק לפקודת מערכת שאושרה), מגבלות זיכרון ו-CPU, בלי תיקיות של המחשב המארח.
- פקודות מערכת, שינוי קוד, מקורות חבילות חריגים ומשתנים שנראים כסודות עוצרים לאישור. הכללים ב-`safety.py`, לא במודל.
- תוכן הפרויקט (README, שגיאות, קבצים) מסומן כנתונים ולא כהוראות.
- בהעתקה מתיקייה לא עוברים `.env`, מפתחות פרטיים, `.git` ו-`.venv`.
- סוד שהמשתמש מזין נכתב ישירות לקונטיינר, ולא נשמר ב-State או ב-LangSmith.
- תצוגה חיה נגישה מהמחשב המקומי בלבד (`127.0.0.1`).

**מגבלה:** לקונטיינר יש גישה לאינטרנט. אין להריץ פרויקט שלא הייתם מוכנים להריץ בסביבה מבודדת עם רשת.

## התקנה

דרישות: Python 3.11 ומעלה, Docker Desktop פועל, Node.js 22 (לממשק), ומפתחות OpenAI ו-LangSmith.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --no-deps -r requirements.lock.txt
copy .env.example .env
```

`requirements.lock.txt` נועל את כל החבילות, כולל תלויות המשנה, לגרסאות שנבדקו (Windows, Python 3.13). `requirements.txt` מפרט רק את הספריות הישירות, והתקנה ממנו עלולה להביא גרסאות אחרות ולהיות איטית.

ממלאים את הערכים ב-`.env`. הקובץ חייב להכיל ASCII בלבד: `langgraph dev` קורא אותו בקידוד של Windows העברי.

**מאחורי NetFree:** במחשב המארח `truststore` משתמש במאגר התעודות של Windows, ולתוך כל קונטיינר הסוכן מזריק את תעודות NetFree.

## הרצה

### ממשק אינטרנט

שני חלונות טרמינל:

```powershell
.\.venv\Scripts\langgraph.exe dev --no-browser --no-reload --allow-blocking
```

```powershell
cd frontend
npm install
npm run dev
```

האתר נפתח ב-http://localhost:5180. אם פורט 2024 תפוס, מוסיפים לפקודה הראשונה `--port 2025`, ולפני `npm run dev` מריצים `$env:LANGGRAPH_URL="http://127.0.0.1:2025"`.

- במסך ההתחלה בוחרים: **רק תוצרים**, **תצוגה חיה** (שרת או חלון, דרך noVNC) או **הקלטת וידאו**.
- תצוגה חיה נשארת פעילה עד "עצור תצוגה", ונסגרת לבד אחרי 30 דקות.
- מבנה הקוד: [frontend/README.md](frontend/README.md).

### שורת פקודה

```powershell
python cli.py evaluation/fixtures/ok_requests_script
```

ריצה שעצרה אפשר להמשיך גם אחרי סגירת התוכנה:

```powershell
python cli.py --resume --thread <מזהה הריצה>
```

התוצרים נשמרים ב-`.reporunner/runs/<מזהה>/`.

### הרחבה ל-GitHub

`extension/` מוסיפה בדפי ריפו כפתור "הרץ עם RepoRunner". [הוראות התקנה](extension/README.md).

## הערכה

הדאטהסט (`evaluation/fixtures/`): 9 פרויקטים תקינים, 12 שבורים, 3 שדורשים אדם ו-2 עם ניסיון הזרקה. המדדים (`evaluators.py`): הצלחה, ניסיונות, חזרה על תיקון, עצירה נכונה, עמידות להזרקה, טוקנים וזמן. בעצירות עונה "אדם מדומה" לפי תשובות מוגדרות מראש.

```powershell
python -m evaluation.run_experiment --label v1
```

```powershell
python -m evaluation.run_experiment --label v2
```

ניסוי מלא עולה כ-125 עד 145 אלף טוקנים. לבדיקה קצרה: `--only <שם דוגמה> --repetitions 1`.

## בדיקות

```powershell
python -m pytest tests
```

חלק מהבדיקות דורשות Docker פועל.

## עמידה בדרישות התרגיל

| # | דרישה | מצב |
|---|---|---|
| 1 | שימוש ב-`langgraph` | ✔ |
| 2 | לולאה / ענף מותנה | ✔ ארבע לולאות |
| 3 | `interrupt` ו-human-in-the-loop | ✔ |
| 4 | דאטהסט והערכה ב-LangSmith, לפני ואחרי שיפור | ✔ |
| 5 | README עם trace ותובנה | ✔ |

## מגבלות ידועות והמשך

- Python בלבד.
- ה-Dockerfile של פרויקט עם חלון לא כולל מסך וירטואלי.
- אימות מוכיח שהפרויקט עולה ורץ, לא שהלוגיקה שלו נכונה.
- פתיחת Pull Request אוטומטית עם התוצרים: מתוכנן, עוד לא ממומש.
