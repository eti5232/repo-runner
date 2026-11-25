import type { RunPhase, RunState } from "@/types/agent";
import { commandOk } from "@/lib/command";

export type StageId = "clone" | "analyze" | "plan" | "execute" | "diagnose" | "fix" | "approval" | "verify" | "report";
export type StageStatus = "done" | "active" | "waiting" | "failed" | "pending";

export type Stage = {
  id: StageId;
  label: string;
  node: string; // שם הצומת בגרף, להצגה קטנה
  status: StageStatus;
  note?: string;
};

const STAGES: { id: StageId; label: string; node: string }[] = [
  { id: "clone", label: "שכפול", node: "clone_repo" },
  { id: "analyze", label: "ניתוח", node: "analyze_project" },
  { id: "plan", label: "תכנון", node: "plan_run" },
  { id: "execute", label: "הרצה", node: "execute_step" },
  { id: "diagnose", label: "אבחון", node: "diagnose_error" },
  { id: "fix", label: "תיקון", node: "propose_fix" },
  { id: "approval", label: "אישור", node: "safety_gate" },
  { id: "verify", label: "אימות", node: "verify" },
  { id: "report", label: "תוצר", node: "report" },
];

/**
 * בונה את "מסלול הסוכן" מתוך ה-State בלבד.
 * הסיבה: ה-State תמיד זמין (גם כשפותחים ריצה ישנה), בניגוד לאירועים חיים של הצמתים.
 */
export function deriveStages(values: RunState, phase: RunPhase): Stage[] {
  const attempts = values.attempt_history?.length ?? 0;
  const done = Boolean(values.report);
  const reached: Record<StageId, boolean> = {
    clone: Boolean(values.container) || done,
    analyze: Boolean(values.profile) || done,
    plan: Boolean(values.plan?.length) || done,
    execute: Boolean(values.last_result) || done,
    diagnose: attempts > 0 || Boolean(values.diagnosis) || done,
    fix: attempts > 0 || done,
    approval: (values.approvals?.length ?? 0) > 0 || phase === "waiting",
    verify: done,
    report: done,
  };
  const retried = attempts > 0 && phase !== "succeeded";
  const lastFailed = values.last_result ? !commandOk(values.last_result) : false;

  const stages: Stage[] = STAGES.map((s) => ({ ...s, status: reached[s.id] ? "done" : "pending" }));
  const byId = Object.fromEntries(stages.map((s) => [s.id, s])) as Record<StageId, Stage>;

  if (phase === "waiting") byId.approval.status = "waiting";
  if (phase === "running" && !done) {
    const active = lastFailed ? "diagnose" : values.last_result ? "execute" : stages.find((s) => s.status === "pending")?.id;
    if (active) byId[active].status = "active";
  }
  if (lastFailed && phase !== "succeeded" && phase !== "running" && byId.execute.status === "done") {
    byId.execute.status = "failed";
  }
  if (phase === "failed") {
    const last = [...stages].reverse().find((s) => s.status === "done");
    if (last) last.status = "failed";
  }
  if (retried) byId.execute.note = `${attempts + 1} ניסיונות`;
  return stages;
}
