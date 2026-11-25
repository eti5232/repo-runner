import type { Approval, Attempt, ProjectProfile, RunState, Step } from "@/types/agent";

export type EventTone = "ok" | "bad" | "warn" | "info";

export type TimelineItem =
  | { kind: "opened"; profile?: ProjectProfile; plan: Step[]; skipped: string[] }
  | { kind: "attempt"; attempt: Attempt }
  | { kind: "event"; tone: EventTone; text: string; code?: string };

export type SafetyStats = { auto: number; approved: number; rejected: number };

/** מתאימה אישור של אדם לניסיון: אותן פקודות תיקון בדיוק. */
function matchesApproval(approval: Approval, attempt: Attempt): boolean {
  return (
    approval.kind === "sensitive_fix" &&
    approval.action === "approve" &&
    approval.detail === attempt.fix_commands.join("; ")
  );
}

/** מסבירה החלטה של אדם שלא קשורה לניסיון מסוים, כשורה בציר הזמן. */
function describeApproval(approval: Approval): TimelineItem {
  if (approval.kind === "secret_needed") {
    return { kind: "event", tone: "ok", text: "סיפקת את הסוד, והוא נכתב לקונטיינר בלבד", code: approval.detail };
  }
  if (approval.kind === "attempts_exhausted") {
    return approval.action === "continue"
      ? { kind: "event", tone: "info", text: "הוספת עוד ניסיונות לסוכן" }
      : { kind: "event", tone: "bad", text: "עצרת את הריצה אחרי שנגמרו הניסיונות" };
  }
  if (approval.action === "reject") return { kind: "event", tone: "warn", text: "דחית את התיקון המוצע", code: approval.detail };
  if (approval.action === "stop") return { kind: "event", tone: "bad", text: "עצרת את הריצה" };
  return { kind: "event", tone: "ok", text: "אישרת את התיקון", code: approval.detail };
}

/**
 * הופכת את ה-State של הריצה לרשימת פריטים בציר הזמן (בסגנון שיחה ב-Pull Request),
 * ומחשבת גם סטטיסטיקה של החלטות הבטיחות לסרגל הצד.
 */
export function buildTimeline(
  values: RunState,
  pendingCommands?: string,
): { items: TimelineItem[]; stats: SafetyStats } {
  const items: TimelineItem[] = [{ kind: "opened", profile: values.profile, plan: values.plan ?? [], skipped: values.skipped ?? [] }];
  const approvals = [...(values.approvals ?? [])];
  const stats: SafetyStats = { auto: 0, approved: 0, rejected: 0 };

  for (const attempt of values.attempt_history ?? []) {
    items.push({ kind: "event", tone: "bad", text: "הפקודה נכשלה", code: attempt.failed_command });
    items.push({ kind: "attempt", attempt });

    const index = approvals.findIndex((approval) => matchesApproval(approval, attempt));
    const rejectedIndex = approvals.findIndex(
      (approval) =>
        approval.kind === "sensitive_fix" && approval.action === "reject" && approval.detail === attempt.fix_commands.join("; "),
    );
    if (pendingCommands !== undefined && attempt.fix_commands.join("; ") === pendingCommands) {
      // התיקון הזה ממתין עכשיו לאישור: ה-State כבר מכיל אותו, אבל עוד לא הוחלט עליו. כרטיס האישור יוצג במקום אירוע.
    } else if (index >= 0) {
      approvals.splice(index, 1);
      stats.approved += 1;
      items.push({ kind: "event", tone: "ok", text: "אישרת את התיקון, והוא הופעל" });
    } else if (rejectedIndex >= 0) {
      approvals.splice(rejectedIndex, 1);
      stats.rejected += 1;
      items.push({ kind: "event", tone: "warn", text: "דחית את התיקון, והסוכן חיפש חלופה" });
    } else {
      stats.auto += 1;
      items.push({ kind: "event", tone: "ok", text: "שער הבטיחות סימן את התיקון כבטוח, והוא הופעל אוטומטית" });
    }
  }

  for (const approval of approvals) {
    items.push(describeApproval(approval));
  }

  if (values.report) {
    items.push({
      kind: "event",
      tone: values.report.succeeded ? "ok" : "bad",
      text: values.report.succeeded ? "הפרויקט עבר אימות והוא רץ" : "הריצה הסתיימה בלי הצלחה",
    });
  }
  return { items, stats };
}
