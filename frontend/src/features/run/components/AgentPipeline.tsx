import { Icon } from "@/components/ui/Icon";
import { cn } from "@/lib/cn";
import type { Stage, StageStatus } from "@/lib/pipeline";

const DOT: Record<StageStatus, string> = {
  done: "bg-green text-white",
  active: "bg-pink text-white animate-pulse",
  waiting: "bg-yellow text-ink animate-ring",
  failed: "bg-red text-white",
  pending: "border-2 border-line-strong bg-canvas",
};

function StageIcon({ status }: { status: StageStatus }) {
  if (status === "done") return <Icon name="check" size={13} strokeWidth={3} />;
  if (status === "failed") return <Icon name="x" size={13} strokeWidth={3} />;
  if (status === "waiting") return <Icon name="alert" size={13} strokeWidth={3} />;
  return null;
}

/** מסלול הסוכן: כל שלב בגרף עם הסטטוס שלו. נבנה מה-State, ולכן עובד גם לריצות ישנות. */
export function AgentPipeline({ stages }: { stages: Stage[] }) {
  return (
    <section className="mt-7 overflow-x-auto rounded-2xl border border-line bg-subtle p-5 shadow-card">
      <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-muted">מסלול הסוכן</p>
      <ol className="flex items-center">
        {stages.map((stage, index) => (
          <li key={stage.id} className="flex flex-1 items-center last:flex-none">
            <div
              title={stage.node}
              className={cn(
                "flex items-center gap-2 rounded-xl border bg-canvas px-2.5 py-2 transition",
                stage.status === "waiting" && "border-yellow-line shadow-[0_6px_20px_-8px_rgb(242_204_12/0.7)]",
                stage.status === "active" && "border-pink/40",
                stage.status === "failed" && "border-red/40",
                (stage.status === "done" || stage.status === "pending") && "border-line",
              )}
            >
              <span className={cn("grid size-[22px] place-items-center rounded-full", DOT[stage.status])}>
                <StageIcon status={stage.status} />
              </span>
              <div className="leading-tight">
                <b className="block whitespace-nowrap text-[13px] font-semibold text-ink">{stage.label}</b>
                {stage.note && <small className="whitespace-nowrap text-[11px] text-muted">{stage.note}</small>}
              </div>
            </div>
            {index < stages.length - 1 && (
              <span className={cn("h-0.5 min-w-2 flex-1", stage.status === "done" ? "bg-green" : "bg-line")} />
            )}
          </li>
        ))}
      </ol>
    </section>
  );
}
