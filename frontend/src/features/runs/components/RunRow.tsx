import { Link } from "react-router-dom";
import type { RunSummary } from "@/api/runs";
import { Avatar } from "@/components/ui/Avatar";
import { Badge, type Tone } from "@/components/ui/Badge";
import { Icon } from "@/components/ui/Icon";
import { relativeTime, repoNameFromSource } from "@/lib/format";
import { derivePhase, PHASE_LABEL } from "@/lib/runPhase";
import type { RunPhase } from "@/types/agent";

const TONE: Record<RunPhase, Tone> = {
  idle: "neutral",
  running: "pink",
  waiting: "yellow",
  succeeded: "green",
  failed: "red",
};

/** שורה אחת ברשימת הריצות. */
export function RunRow({ run }: { run: RunSummary }) {
  const phase = derivePhase(run.state, {
    isLoading: run.threadStatus === "busy",
    waiting: run.threadStatus === "interrupted",
  });
  const name = repoNameFromSource(run.source);
  const fixes = run.state.attempt_history?.length ?? 0;

  return (
    <Link
      to={`/runs/${run.id}`}
      className="flex items-center gap-4 border-b border-line px-5 py-4 no-underline transition last:border-b-0 hover:bg-subtle"
    >
      <Avatar label={name.slice(0, 2).toUpperCase()} kind="repo" size={40} />
      <div className="min-w-0 flex-1">
        <p className="ltr truncate text-left font-semibold text-ink">{name}</p>
        <p className="text-[13px] text-muted">
          {relativeTime(run.updatedAt)}
          {fixes > 0 && ` · ${fixes} תיקונים`}
        </p>
      </div>
      <Badge tone={TONE[phase]}>{PHASE_LABEL[phase]}</Badge>
      <Icon name="chevron" className="rotate-180 text-muted" />
    </Link>
  );
}
