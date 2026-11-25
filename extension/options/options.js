// דף ההגדרות של ההרחבה: שומר את הכתובת שבה האתר של RepoRunner רץ.

const DEFAULT_APP_URL = "http://localhost:5180";
const input = document.getElementById("app-url");
const status = document.getElementById("status");

/**
 * 1. מקבלת: כלום.
 * 2. מחזירה: Promise.
 * 3. עושה: טוענת את הכתובת השמורה ומציגה אותה בשדה.
 */
async function load() {
  const { appUrl } = await chrome.storage.sync.get({ appUrl: DEFAULT_APP_URL });
  input.value = appUrl;
}

/**
 * 1. מקבלת: כלום.
 * 2. מחזירה: Promise.
 * 3. עושה: שומרת את הכתובת מהשדה (או את ברירת המחדל אם ריק) ומציגה אישור קצר.
 */
async function save() {
  await chrome.storage.sync.set({ appUrl: input.value.trim() || DEFAULT_APP_URL });
  status.textContent = "נשמר";
  setTimeout(() => (status.textContent = ""), 1500);
}

document.getElementById("save").addEventListener("click", save);
void load();
