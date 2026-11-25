// סקריפט שרץ בתוך דפי github.com. מוסיף כפתור "הרץ עם RepoRunner" בדפי ריפו.
// הכפתור פותח את האתר של הסוכן עם ?source=<קישור הריפו>, והמשתמשת רק לוחצת "הפעל".

const BUTTON_ID = "reporunner-button";
const DEFAULT_APP_URL = "http://localhost:5180";
const LOGO_SVG =
  '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" ' +
  'stroke-linecap="round" aria-hidden="true"><path d="M7 4v16l13-8z"/></svg>';

/**
 * 1. מקבלת: כלום.
 * 2. מחזירה: "owner/repo" של הדף הנוכחי, או null אם זה לא דף ריפו.
 * 3. עושה: קוראת את שם הריפו מתג ה-meta ש-GitHub שם בכל דף ריפו (יציב יותר מפענוח הכתובת).
 */
function repoFromPage() {
  const meta = document.querySelector('meta[name="octolytics-dimension-repository_nwo"]');
  return meta ? meta.content : null;
}

/**
 * 1. מקבלת: כלום.
 * 2. מחזירה: Promise עם כתובת האתר של RepoRunner, בלי '/' בסוף.
 * 3. עושה: קוראת את הכתובת ששמרה המשתמשת בהגדרות ההרחבה (ברירת מחדל: localhost:5180).
 */
async function getAppUrl() {
  const { appUrl } = await chrome.storage.sync.get({ appUrl: DEFAULT_APP_URL });
  return appUrl.replace(/\/+$/, "");
}

/**
 * 1. מקבלת: appUrl (כתובת האתר) ו-repo (בצורת owner/repo).
 * 2. מחזירה: הקישור המלא שפותח את האתר עם הריפו מוזן.
 * 3. עושה: בונה את הכתובת עם הקישור לריפו כפרמטר.
 */
function buildLink(appUrl, repo) {
  return `${appUrl}/?source=${encodeURIComponent(`https://github.com/${repo}`)}`;
}

/**
 * 1. מקבלת: כלום.
 * 2. מחזירה: אלמנט <a> של הכפתור (ללא קישור עדיין).
 * 3. עושה: יוצרת את הכפתור. עוגן רגיל ולא כפתור, כדי שפתיחה בטאב חדש תעבוד כמו בכל קישור (גם קליק אמצעי).
 */
function createButton() {
  const link = document.createElement("a");
  link.id = BUTTON_ID;
  link.className = "reporunner-button";
  link.target = "_blank";
  link.rel = "noopener";
  link.innerHTML = `${LOGO_SVG}<span>הרץ עם RepoRunner</span>`;
  return link;
}

/**
 * 1. מקבלת: כלום.
 * 2. מחזירה: רשימת כפתורי הפעולות של הריפו (<ul>), או null אם עוד לא נטענה.
 * 3. עושה: מוצאת את הרשימה לפי כפתור ה-Fork, עם גיבוי למבנה הישן של GitHub.
 */
function findActions() {
  return (
    document.querySelector('[data-testid="fork-button"]')?.closest("ul") ?? document.querySelector("ul.pagehead-actions")
  );
}

/**
 * 1. מקבלת: button (אלמנט הכפתור).
 * 2. מחזירה: כלום.
 * 3. עושה: מוסיפה את הכפתור לשורת הפעולות של הריפו (Notifications, Fork, Star). מזהה אותה לפי כפתור ה-Fork
 *    (data-testid יציב יותר ממחלקות העיצוב של GitHub), ועם גיבוי למבנה הישן. אם אין שורה כזו, מציבה
 *    אותו בפינת המסך, כך שהוא תמיד זמין.
 */
function placeButton(button) {
  const actions = findActions();
  if (actions) {
    const item = document.createElement("li");
    item.className = "reporunner-item";
    item.appendChild(button);
    actions.prepend(item);
  } else {
    button.classList.add("reporunner-floating");
    document.body.appendChild(button);
  }
}

/**
 * 1. מקבלת: כלום.
 * 2. מחזירה: Promise.
 * 3. עושה: מוודאת שיש כפתור אחד, ורק בדפי ריפו. בדף שאינו ריפו מסירה אותו. בטוחה להרצה חוזרת.
 */
async function ensureButton() {
  const repo = repoFromPage();
  const existing = document.getElementById(BUTTON_ID);

  if (!repo) {
    existing?.closest(".reporunner-item")?.remove();
    existing?.remove();
    return;
  }

  const href = buildLink(await getAppUrl(), repo);
  if (existing) {
    existing.href = href; // ייתכן שעברנו לריפו אחר באותה טעינה (GitHub מחליף דפים בלי לרענן)
    // GitHub בונה את הכותרת אחרי שהדף נטען: אם הכפתור הוצב בגיבוי וכעת יש שורת פעולות, מעבירים אותו אליה
    if (existing.classList.contains("reporunner-floating") && findActions()) {
      existing.classList.remove("reporunner-floating");
      placeButton(existing);
    }
    return;
  }
  const button = createButton();
  button.href = href;
  placeButton(button);
}

// GitHub טוען דפים בלי רענון מלא, ולכן מאזינים לניווט שלו ולשינויים בדף (עם השהיה קצרה למניעת עומס)
let pending = 0;
const schedule = () => {
  clearTimeout(pending);
  pending = setTimeout(ensureButton, 150);
};
document.addEventListener("turbo:render", schedule);
document.addEventListener("turbo:load", schedule);
new MutationObserver(schedule).observe(document.body, { childList: true, subtree: true });
chrome.storage.onChanged.addListener(schedule); // שינוי כתובת האתר בהגדרות
ensureButton();
