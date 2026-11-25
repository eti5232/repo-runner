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

/** בודקת שהשרת של הסוכן זמין. */
export async function pingServer(): Promise<boolean> {
  try {
    const response = await fetch(`${LANGGRAPH_URL}/ok`);
    return response.ok;
  } catch {
    return false;
  }
}
