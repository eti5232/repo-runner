import { LANGGRAPH_URL } from "@/config/env";

/** כתובת מלאה לקובץ ההקלטה בשרת (הנתיב שהסוכן החזיר יחסי לשרת). */
export function recordingUrl(path: string): string {
  return `${LANGGRAPH_URL}${path}`;
}

/** סוגרת קונטיינר שמריץ תצוגה חיה (reporunner/preview_routes.py). */
export async function stopPreview(container: string): Promise<void> {
  await fetch(`${LANGGRAPH_URL}/reporunner/stop`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ container }),
  });
}
