import type { DiagnosisCategory, RiskKind } from "@/types/agent";

/** תוויות בעברית לסוגי השגיאות שהסוכן מאבחן. */
export const CATEGORY_LABEL: Record<DiagnosisCategory, string> = {
  missing_package: "חבילה חסרה",
  version_conflict: "התנגשות גרסאות",
  missing_system_library: "ספריית מערכת חסרה",
  missing_env_var: "משתנה סביבה חסר",
  missing_file: "קובץ חסר",
  python_version: "גרסת Python",
  code_bug: "באג בקוד",
  other: "שגיאה אחרת",
};

export function categoryLabel(category: string): string {
  return CATEGORY_LABEL[category as DiagnosisCategory] ?? category;
}

/** למה תיקון דורש אישור אדם. */
export const RISK_LABEL: Record<RiskKind, string> = {
  system: "פקודת מערכת (משנה את הקונטיינר)",
  remote_script: "הורדה והרצה של סקריפט מהרשת",
  secret: "משתנה סביבה שנראה כמו סוד",
  code_change: "שינוי בקוד המקור של הפרויקט",
  custom_source: "התקנה ממקור חבילות מותאם",
  repeated: "תיקון שכבר נוסה",
  outside: "פעולה מחוץ לתיקיית הפרויקט",
  unrecognized: "פקודה שלא ברשימת הפקודות המוכרות",
};

/** הסבר פשוט לכל סוג סיכון: מה זה אומר, ואיך כדאי להחליט. כתוב בקוד קבוע, כך שהוא תמיד ברור ואמין. */
export const RISK_HELP: Record<RiskKind, string> = {
  system: "מתקינה תוכנה בתוך הקונטיינר בלבד, לא במחשב שלך. בדרך כלל בטוח לאשר אם התוכנה מוכרת לך.",
  remote_script: "מורידה קוד מהאינטרנט ומריצה אותו מיד. זה מסוכן: אשרי רק אם את סומכת על המקור.",
  secret: "מגדירה ערך שנראה כמו סוד (מפתח או סיסמה). בדקי שהפרויקט באמת צריך אותו.",
  code_change: "משנה קובץ קוד של הפרויקט בתוך הקונטיינר. הקובץ המקורי שלך לא משתנה. אשרי אם השינוי ברור לך.",
  repeated: "הסוכן מציע שוב תיקון שכבר נוסה ולא פתר את הבעיה. עדיף לדחות, או לעצור ולבדוק את הפרויקט.",
  custom_source: "מתקינה חבילות ממקור לא רגיל. בדקי שהכתובת מוכרת לך.",
  outside: "פועלת מחוץ לתיקיית הפרויקט. אם היא לא מוכרת לך, עדיף לדחות.",
  unrecognized: "פקודה שהמערכת לא מכירה. קראי אותה היטב לפני שמאשרים.",
};

/** מה הסוכן עושה עכשיו, לפי שם הצומת בגרף. */
export const NODE_LABEL: Record<string, string> = {
  clone_repo: "משכפל את הפרויקט",
  analyze_project: "מנתח את הפרויקט",
  plan_run: "בונה תוכנית הרצה",
  execute_step: "מריץ פקודה בקונטיינר",
  verify: "בודק שהפרויקט באמת עובד",
  diagnose_error: "מאבחן את השגיאה",
  investigate: "קורא קבצים כדי להבין",
  propose_fix: "מציע תיקון",
  switch_python: "מחליף גרסת Python",
  safety_gate: "בודק בטיחות",
  apply_fix: "מחיל את התיקון",
  human_approval: "ממתין להחלטה שלך",
  report: "בונה את התוצרים",
};
