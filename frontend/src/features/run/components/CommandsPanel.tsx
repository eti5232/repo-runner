import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader } from "@/components/ui/Card";
import { Icon } from "@/components/ui/Icon";
import { commandOk, commandOutput } from "@/lib/command";
import { formatDuration } from "@/lib/format";
import type { RunState } from "@/types/agent";

/** הפקודות שבתוכנית ההרצה, והפלט של הפקודה האחרונה שרצה בקונטיינר. */
export function CommandsPanel({ values }: { values: RunState }) {
  const plan = values.plan ?? [];
  const last = values.last_result;
  const nextIndex = values.step_index ?? 0;

  if (plan.length === 0) {
    return <p className="py-10 text-center text-muted">התוכנית עוד לא נבנתה.</p>;
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader title="תוכנית ההרצה" aside={<Badge>{plan.length} צעדים</Badge>} />
        <ol>
          {plan.map((step, index) => {
            const failedHere = last && !commandOk(last) && last.command === step.command;
            const done = index < nextIndex && !failedHere;
            return (
              <li key={`${index}-${step.command}`} className="flex items-center gap-3.5 border-b border-line px-5 py-3.5 last:border-b-0">
                <span
                  className={`grid size-6 shrink-0 place-items-center rounded-full ${
                    failedHere ? "bg-red text-white" : done ? "bg-green text-white" : "border-2 border-line-strong"
                  }`}
                >
                  {failedHere ? <Icon name="x" size={12} strokeWidth={3} /> : done ? <Icon name="check" size={12} strokeWidth={3} /> : null}
                </span>
                <div className="min-w-0 flex-1">
                  <code className="block truncate text-[13px] text-ink">{step.command}</code>
                  <span className="text-[12.5px] text-muted">{step.purpose}</span>
                </div>
                {step.is_fix && <Badge tone="pink">תיקון</Badge>}
                {step.as_root && <Badge tone="yellow">root</Badge>}
              </li>
            );
          })}
        </ol>
      </Card>

      {last && (
        <Card>
          <CardHeader
            title="הפלט האחרון"
            aside={
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted">{formatDuration(last.duration_sec)}</span>
                <Badge tone={commandOk(last) ? "green" : "red"}>{commandOk(last) ? "קוד 0" : `קוד ${last.exit_code}`}</Badge>
              </div>
            }
          />
          <pre className="ltr max-h-[360px] overflow-auto whitespace-pre-wrap bg-subtle p-5 text-left text-[12.5px] leading-relaxed text-ink-2">
            <span className="text-muted">$ {last.command}</span>
            {"\n"}
            {commandOutput(last) || "(אין פלט)"}
          </pre>
        </Card>
      )}
    </div>
  );
}
