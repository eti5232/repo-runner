import { LANGGRAPH_URL } from "@/config/env";

/**
 * שולחת סוד ישירות לקונטיינר (reporunner/secrets_route.py), מחוץ לגרף.
 * הערך לא נכנס ל-State, ל-checkpointer או ל-LangSmith.
 */
export async function sendSecret(container: string, name: string, value: string): Promise<void> {
  const response = await fetch(`${LANGGRAPH_URL}/reporunner/secret`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ container, name, value }),
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { error?: string };
    throw new Error(body.error ?? "שמירת הסוד נכשלה");
  }
}
