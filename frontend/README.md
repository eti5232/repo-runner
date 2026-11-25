# RepoRunner: הממשק (React)

ממשק אינטרנט לסוכן. הוא מדבר ישירות עם שרת LangGraph (`langgraph dev`) ומציג ריצה חיה: מסלול הסוכן, ניסיונות תיקון, עצירות לאישור, פקודות ותוצרים.

**טכנולוגיות:** React 19, TypeScript, Vite, Tailwind CSS 4, React Router, `@langchain/langgraph-sdk` (`useStream`).

## הרצה

שני תהליכים במקביל. מתיקיית הפרויקט הראשית:

```powershell
.\.venv\Scripts\langgraph.exe dev --no-browser --no-reload --allow-blocking
```

ומתיקיית `frontend`:

```powershell
npm install
npm run dev
```

האתר נפתח ב-http://localhost:5180. הפרוקסי `/lg` (ב-`vite.config.ts`) מעביר את הבקשות לשרת של LangGraph בפורט 2024.

> `--no-reload` חשוב: בלי זה השרת מתאתחל בכל שינוי בקבצי `node_modules`.

## מבנה התיקיות

```
src/
├── main.tsx                 נקודת הכניסה
├── index.css                טוקנים של עיצוב (צבעים, גופנים, צללים, אנימציות)
├── app/                     הרכבת האפליקציה והנתיבים (routes.tsx)
├── config/                  הגדרות חיבור (כתובת השרת, שם הגרף)
├── types/                   טיפוסים שמשקפים את מודלי הסוכן ב-Python
├── api/                     כל הקריאות לשרת: לקוח, ריצות, סודות
├── lib/                     פונקציות טהורות: עיצוב טקסט, שלב הריצה, מסלול הסוכן
├── hooks/                   hooks משותפים (חיבור לשרת)
├── components/
│   ├── ui/                  אבני בניין ללא לוגיקה: Button, Badge, Card, CodeBlock, Icon...
│   └── layout/              מסגרת האתר: AppShell, SiteHeader, PageContainer
└── features/                כל מסך כתיקייה עצמאית
    ├── start/               מסך הבית: הדבקת קישור והפעלה
    ├── runs/                רשימת כל הריצות
    └── run/                 מסך הריצה (הליבה)
        ├── hooks/           useAgentRun: החיבור לסוכן
        ├── lib/             בניית ציר הזמן, תוויות בעברית
        └── components/      שיחה, ניסיונות, כרטיס אישור, פקודות, תוצרים, סרגל צד
```

**כלל הארכיטקטורה:** `components/ui` לא יודע כלום על הסוכן; `features` משתמשים בו. כל הידע על השרת נמצא ב-`api/` וב-`useAgentRun`, ולכן שינוי בשרת נוגע במקום אחד.

## איך זה מתחבר לסוכן

1. **התחלה:** מסך הבית יוצר thread בשרת (`createRun`) ועובר ל-`/runs/:threadId`. מסך הריצה מפעיל את הסוכן עם `{source}`.
2. **ריצה חיה:** `useStream` מזרים את ה-State. הממשק בונה ממנו הכול (מסלול הסוכן, ציר הזמן, סטטיסטיקות), ולכן גם ריצות ישנות נפתחות נכון.
3. **עצירה לאישור:** כשהגרף קורא ל-`interrupt()`, `stream.interrupt` מכיל את השאלה. הכרטיס שולח תשובה עם `Command(resume=...)`.
4. **סודות:** הערך נשלח לנקודת הקצה `/reporunner/secret` (`reporunner/secrets_route.py`), שכותבת אותו ישירות לקונטיינר. הערך לא נכנס ל-State, ל-checkpointer או ל-LangSmith, ורק אחר כך הגרף מקבל `{"action": "provided"}`.

## בדיקות

```powershell
npx tsc -b      # בדיקת טיפוסים
npm run build   # בנייה
```
