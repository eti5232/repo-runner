import { client } from "@/api/client";
import { LANGGRAPH_URL } from "@/config/env";
import type { RunState } from "@/types/agent";

/** סיכום של ריצה אחת לרשימת הריצות. */
export type RunSummary = {
  id: string;
  source: string | undefined;
  threadStatus: "idle" | "busy" | "interrupted" | "error";
  state: RunState;
  updatedAt: string;
};

/** פותחת thread חדש בשרת. ה-thread הוא "ריצה" אחת עם הזיכרון שלה. */
export async function createRun(): Promise<string> {
  const thread = await client.threads.create();
  return thread.thread_id;
}

/** מחזירה את הריצות האחרונות, החדשות ראשונות. */
export async function listRuns(limit = 50): Promise<RunSummary[]> {
  const threads = await client.threads.search<RunState>({
    limit,
    sortBy: "updated_at",
    sortOrder: "desc",
  });
  return threads
    .filter((t) => t.values && "source" in t.values)
    .map((t) => ({
      id: t.thread_id,
      source: t.values.source,
      threadStatus: t.status,
      state: t.values,
      updatedAt: t.updated_at,
    }));
}

/** מצב הריצה בשרת, ואם נכשלה גם הודעת השגיאה שלה. */
export async function runOutcome(threadId: string): Promise<{ status: RunSummary["threadStatus"]; error: string | null }> {
  const thread = await client.threads.get(threadId);
  if (thread.status !== "error") return { status: thread.status, error: null };
  const state = await client.threads.getState(threadId);
  const failed = state.tasks?.find((task) => task.error);
  return { status: thread.status, error: failed?.error ?? "" };
}

/** מבטלת בשרת את כל הריצות הפעילות של ה-thread (לא רק את ההאזנה בדפדפן). */
export async function cancelActiveRuns(threadId: string): Promise<void> {
  const runs = await client.runs.list(threadId);
  const active = runs.filter((run) => run.status === "running" || run.status === "pending");
  await Promise.all(active.map((run) => client.runs.cancel(threadId, run.run_id)));
  // ביטול בשרת לא מוחק את הקונטיינר, ולכן מבקשים את זה בנפרד (reporunner/preview_routes.py)
  await fetch(`${LANGGRAPH_URL}/reporunner/cancel`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ thread_id: threadId }),
  });
}

/** בודקת שהשרת של הסוכן זמין. */
export async function pingServer(): Promise<boolean> {
  try {
    const response = await fetch(`${LANGGRAPH_URL}/ok`);
    return response.ok;
  } catch {
    return false;
  }
}
