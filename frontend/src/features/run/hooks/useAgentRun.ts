import { useEffect, useState } from "react";
import { useStream } from "@langchain/langgraph-sdk/react";
import { client } from "@/api/client";
import { AGENT_VERSION, ASSISTANT_ID, LANGGRAPH_URL, RECURSION_LIMIT } from "@/config/env";
import { derivePhase } from "@/lib/runPhase";
import type { ApprovalAnswer, ApprovalRequest, PreviewMode, RunPhase, RunState } from "@/types/agent";

/** הגדרות הריצה שנשלחות לשרת: איזו גרסת סוכן. חייבות להישלח גם בהמשך אחרי עצירה. */
const RUN_CONTEXT = { agent_version: AGENT_VERSION };

export type AgentRun = {
  values: RunState;
  phase: RunPhase;
  /** מה שהסוכן שואל כרגע, או undefined אם הוא לא ממתין */
  approval: ApprovalRequest | undefined;
  /** שם הצומת שרץ עכשיו (מאירועים חיים) */
  currentNode: string | null;
  loading: boolean;
  /** הודעת שגיאה אם הריצה נכשלה בשרת, אחרת null */
  failure: string | null;
  start: (source: string, previewMode: PreviewMode) => void;
  answer: (answer: ApprovalAnswer) => void;
  stop: () => void;
};

/**
 * החיבור לסוכן: עוטף את useStream של LangGraph.
 * נותן למסכים: ה-State החי, השלב הנוכחי, השאלה לאדם (אם יש), ופעולות להתחלה, מענה ועצירה.
 */
export function useAgentRun(threadId: string): AgentRun {
  const [currentNode, setCurrentNode] = useState<string | null>(null);

  const stream = useStream<RunState>({
    assistantId: ASSISTANT_ID,
    apiUrl: LANGGRAPH_URL,
    threadId,
    reconnectOnMount: true,
    onUpdateEvent: (data) => {
      const node = Object.keys(data as Record<string, unknown>)[0];
      if (node) setCurrentNode(node);
    },
    onFinish: () => setCurrentNode(null),
  });

  // הריצה יכולה להיכשל בשרת (למשל שכפול שנכשל). בלי בדיקה כזו המסך נשאר "טוען" לנצח
  const [threadFailed, setThreadFailed] = useState(false);
  useEffect(() => {
    let cancelled = false;
    client.threads
      .get(threadId)
      .then((thread) => !cancelled && setThreadFailed(thread.status === "error"))
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [threadId, stream.isLoading]);
  const failure = stream.error
    ? String(stream.error instanceof Error ? stream.error.message : stream.error)
    : threadFailed
      ? "הריצה נכשלה בשרת. הפרטים ביומן של שרת LangGraph."
      : null;

  const approval = stream.interrupt?.value as ApprovalRequest | undefined;
  const values = (stream.values ?? {}) as RunState;
  const phase = derivePhase(values, { isLoading: stream.isLoading, waiting: Boolean(approval) });

  return {
    values,
    phase,
    approval,
    currentNode,
    loading: stream.isThreadLoading,
    failure,
    start: (source, previewMode) =>
      void stream.submit({ source, preview_mode: previewMode }, { config: { recursion_limit: RECURSION_LIMIT }, context: RUN_CONTEXT }),
    answer: (answer) =>
      void stream.submit(null, { command: { resume: answer }, config: { recursion_limit: RECURSION_LIMIT }, context: RUN_CONTEXT }),
    stop: () => void stream.stop(),
  };
}
