import { useEffect, useState } from "react";
import { useStream } from "@langchain/langgraph-sdk/react";
import { cancelActiveRuns, runOutcome } from "@/api/runs";
import { AGENT_VERSION, ASSISTANT_ID, LANGGRAPH_URL, RECURSION_LIMIT } from "@/config/env";
import { errorText } from "@/features/run/lib/errorText";
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
  /** הריצה נעצרה לפני שהסתיימה (ע"י המשתמשת או כי השרת הופעל מחדש) */
  stopped: boolean;
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

  // הריצה יכולה להיכשל או להיעצר בשרת. בלי בדיקה כזו המסך נשאר "טוען" לנצח
  const [outcome, setOutcome] = useState<{ status: string; error: string | null } | null>(null);
  const [cancelled, setCancelled] = useState(false);
  useEffect(() => {
    let ignore = false;
    const check = () =>
      runOutcome(threadId)
        .then((result) => !ignore && setOutcome(result))
        .catch(() => undefined);
    void check();
    const timer = window.setInterval(check, 5000);
    return () => {
      ignore = true;
      window.clearInterval(timer);
    };
  }, [threadId, stream.isLoading]);
  const failure =
    outcome?.status === "error"
      ? errorText(outcome.error || "הריצה נכשלה בשרת. הפרטים ביומן של שרת LangGraph.")
      : stream.error
        ? errorText(String(stream.error instanceof Error ? stream.error.message : stream.error))
        : null;

  const approval = stream.interrupt?.value as ApprovalRequest | undefined;
  const values = (stream.values ?? {}) as RunState;
  // "busy" מהשרת: ריצה שנפתחה מחדש בזמן השכפול, כשעוד אין State, היא עדיין ריצה פעילה
  const busy = stream.isLoading || outcome?.status === "busy";
  const phase = derivePhase(values, { isLoading: busy, waiting: Boolean(approval) });

  // יש קלט, אין תוצאה ואין שאלה, והשרת לא עובד על הריצה: היא נעצרה באמצע
  const unfinished = Boolean(values.source) && !values.report && !approval && !failure;
  const stopped = unfinished && (cancelled || (outcome?.status === "idle" && !stream.isLoading && !stream.isThreadLoading));

  return {
    values,
    phase,
    approval,
    currentNode,
    loading: stream.isThreadLoading,
    failure,
    stopped,
    start: (source, previewMode) =>
      void stream.submit({ source, preview_mode: previewMode }, { config: { recursion_limit: RECURSION_LIMIT }, context: RUN_CONTEXT }),
    answer: (answer) =>
      void stream.submit(null, { command: { resume: answer }, config: { recursion_limit: RECURSION_LIMIT }, context: RUN_CONTEXT }),
    stop: () => {
      setCancelled(true);
      void stream.stop();
      void cancelActiveRuns(threadId).catch(() => undefined);
    },
  };
}
