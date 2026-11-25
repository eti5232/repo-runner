import type { RunPhase, RunState } from "@/types/agent";

/**
 * קובעת באיזה שלב הריצה נמצאת.
 * סדר הבדיקות חשוב: תוצאה סופית גוברת, אחריה עצירה לאישור, ואז ריצה פעילה.
 */
export function derivePhase(values: RunState, opts: { isLoading: boolean; waiting: boolean }): RunPhase {
  if (values.report?.succeeded || values.status === "succeeded") return "succeeded";
  if (values.status === "failed" || (values.report && !values.report.succeeded)) return "failed";
  if (opts.waiting) return "waiting";
  if (opts.isLoading || values.container) return "running";
  return "idle";
}

/** תווית ותגית צבע לכל שלב, לשימוש כללי בכל המסכים. */
export const PHASE_LABEL: Record<RunPhase, string> = {
  idle: "מוכן",
  running: "רץ",
  waiting: "ממתין לאישור",
  succeeded: "הצליח",
  failed: "נכשל",
};
