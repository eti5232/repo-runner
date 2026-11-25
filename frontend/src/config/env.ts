/** הגדרות חיבור לשרת של LangGraph. כתובת ברירת המחדל עוברת בפרוקסי של Vite (ראו vite.config.ts). */
export const LANGGRAPH_URL: string =
  import.meta.env.VITE_LANGGRAPH_URL ?? `${window.location.origin}/lg`;

/** שם הגרף כפי שמוגדר ב-langgraph.json */
export const ASSISTANT_ID = "reporunner";

/** גבול הצעדים של LangGraph. ברירת המחדל (25) קורסת בריצה עם כמה תיקונים. */
export const RECURSION_LIMIT = 250;

/** גרסת הסוכן שהאתר מפעיל: v2 היא v1 עם שיפורים (למשל פקודות קצרות). ראו reporunner/context.py. */
export const AGENT_VERSION = "v2";
