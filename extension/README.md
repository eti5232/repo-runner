# RepoRunner for GitHub (הרחבת דפדפן)

מוסיפה לכל דף ריפו ב-github.com כפתור ירוק **"הרץ עם RepoRunner"**. לחיצה פותחת את האתר של הסוכן עם הקישור לריפו כבר מוזן, ומשם בוחרים תצוגה ולוחצים "הפעל".

## התקנה (Chrome או Edge)

1. פותחים `chrome://extensions` (ב-Edge: `edge://extensions`).
2. מפעילים **Developer mode** (מצב מפתח).
3. לוחצים **Load unpacked** ובוחרים את התיקייה `extension` הזו.
4. נכנסים לכל ריפו ב-github.com: הכפתור מופיע בשורת הפעולות (Watch, Fork, Star), או בפינה השמאלית התחתונה אם GitHub שינה את מבנה הדף.

האתר של RepoRunner צריך לרוץ (ראו README הראשי). אם הוא לא ב-`http://localhost:5180`, משנים את הכתובת בהגדרות ההרחבה (Details, ואז Extension options).

## מבנה

```
extension/
├── manifest.json          הגדרת ההרחבה (Manifest V3)
├── content/
│   ├── content.js         מוסיף את הכפתור בדפי ריפו (עובד גם כש-GitHub מחליף דף בלי רענון)
│   └── content.css        עיצוב הכפתור
└── options/               הגדרת כתובת האתר
```

הקישור נשלח כפרמטר `?source=` בכתובת האתר ולא לשום שרת חיצוני, ולכן שום מידע לא יוצא מהמחשב.
