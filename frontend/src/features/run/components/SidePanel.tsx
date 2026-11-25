import type { ReactNode } from "react";
import { Avatar } from "@/components/ui/Avatar";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Icon } from "@/components/ui/Icon";
import type { AgentRun } from "@/features/run/hooks/useAgentRun";
import type { SafetyStats } from "@/features/run/lib/buildTimeline";

type SidePanelProps = { run: AgentRun; stats: SafetyStats };

/** סרגל צד: סוקרים, החלטות בטיחות, תגיות, סביבה ו-Pull request מקושר. */
export function SidePanel({ run, stats }: SidePanelProps) {
  const { values, phase } = run;
  const waiting = phase === "waiting" ? 1 : 0;
  const attempts = values.attempt_history?.length ?? 0;

  return (
    <aside className="space-y-4">
      <Panel title="סוקרים">
        <div className="flex items-center gap-2.5 text-sm">
          <Avatar label="את" size={28} />
          <span className="text-ink">את</span>
          {waiting === 1 && <Badge tone="yellow" className="ms-auto">ממתינה לסקירה</Badge>}
        </div>
      </Panel>

      <Panel title="החלטות בטיחות">
        <div className="grid grid-cols-3 text-center">
          <Stat value={stats.auto + stats.approved} label="הופעלו" tone="text-green" />
          <Stat value={waiting} label="ממתין" tone="text-yellow-deep" divided />
          <Stat value={stats.rejected} label="נדחו" tone="text-ink" divided />
        </div>
      </Panel>

      <Panel title="תגיות">
        <div className="flex flex-wrap gap-1.5">
          {values.profile && <Badge tone="yellow">python {values.profile.python_version}</Badge>}
          {attempts > 0 && <Badge tone="pink">{attempts} תיקונים</Badge>}
          {waiting === 1 && <Badge tone="orange">needs-approval</Badge>}
          {phase === "succeeded" && <Badge tone="green">verified</Badge>}
        </div>
      </Panel>

      <Panel title="סביבה">
        <dl className="space-y-1.5 text-[13.5px]">
          <Row label="קונטיינר" value={values.container?.replace("reporunner-", "")} />
          <Row label="קובץ תלויות" value={values.profile?.deps_file ?? undefined} />
          <Row label="נקודת כניסה" value={values.profile?.entrypoint ?? undefined} />
          <Row label="בדיקות" value={values.profile ? (values.profile.has_tests ? "יש" : "אין") : undefined} plain />
        </dl>
      </Panel>

      <Panel title="Pull request מקושר">
        <p className="text-[13px] text-muted">עדיין אין. אחרי אימות אפשר יהיה לפתוח PR עם ה-Dockerfile.</p>
        <Button disabled className="mt-3 w-full" icon={<Icon name="branch" size={15} />}>
          פתח Pull request
        </Button>
      </Panel>
    </aside>
  );
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-2xl border border-line bg-canvas p-4 shadow-card">
      <h6 className="mb-3 text-xs font-semibold uppercase tracking-widest text-muted">{title}</h6>
      {children}
    </section>
  );
}

function Stat({ value, label, tone, divided }: { value: number; label: string; tone: string; divided?: boolean }) {
  return (
    <div className={divided ? "border-s border-line" : ""}>
      <b className={`block text-[28px] font-semibold leading-none tracking-tight ${tone}`}>{value}</b>
      <small className="text-xs text-muted">{label}</small>
    </div>
  );
}

function Row({ label, value, plain }: { label: string; value: string | undefined; plain?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <dt className="text-muted">{label}</dt>
      <dd>
        {value === undefined ? (
          <span className="text-line-strong">—</span>
        ) : plain ? (
          <span className="text-ink">{value}</span>
        ) : (
          <code className="rounded bg-inset px-1.5 py-0.5 text-xs">{value}</code>
        )}
      </dd>
    </div>
  );
}
