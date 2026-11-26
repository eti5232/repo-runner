import { Badge, type Tone } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Icon } from "@/components/ui/Icon";
import { Spinner } from "@/components/ui/Spinner";
import type { AgentRun } from "@/features/run/hooks/useAgentRun";
import { PHASE_LABEL } from "@/lib/runPhase";
import type { RunPhase } from "@/types/agent";

const TONE: Record<RunPhase, Tone> = {
  idle: "neutral",
  running: "pink",
  waiting: "yellow",
  succeeded: "green",
  failed: "red",
};

/** כותרת הריצה: שם, סטטוס, מונה ניסיונות ופעולות כלליות. */
export function RunHeader({ run }: { run: AgentRun }) {
  const attempts = run.values.attempts ?? 0;
  const limit = run.values.attempt_limit ?? 8;
  const ended = Boolean(run.failure) || run.stopped;

  return (
    <div className="flex items-start justify-between gap-6">
      <div>
        <h2 className="text-[30px] font-semibold leading-tight tracking-tight text-ink">הפוך את הפרויקט לרץ</h2>
        <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-muted">
          <Badge tone={ended ? "red" : TONE[run.phase]} className="px-3 py-0.5 text-[13px] font-semibold">
            {run.phase === "running" && !ended && <Spinner className="size-3" />}
            {ended ? "נעצר" : PHASE_LABEL[run.phase]}
          </Badge>
          {run.phase === "succeeded" || run.phase === "failed" ? (
            <span>
              הסתיים אחרי <b className="font-semibold text-ink">{run.values.attempt_history?.length ?? 0}</b> תיקונים
            </span>
          ) : (
            <span>
              ניסיון <b className="font-semibold text-ink">{Math.min(attempts + 1, limit)}</b> מתוך {limit}
            </span>
          )}
          {run.values.profile && (
            <span className="ltr">
              Python <b className="font-semibold text-ink">{run.values.profile.python_version}</b>
            </span>
          )}
        </div>
      </div>
      {run.phase === "running" && !ended && (
        <Button variant="danger" onClick={run.stop} icon={<Icon name="stop" size={14} />}>
          עצור ריצה
        </Button>
      )}
    </div>
  );
}
