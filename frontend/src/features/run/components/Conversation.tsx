import { Badge } from "@/components/ui/Badge";
import { RichText } from "@/components/ui/RichText";
import { ApprovalCard } from "@/features/run/components/approval/ApprovalCard";
import { AttemptCard } from "@/features/run/components/AttemptCard";
import { BotComment } from "@/features/run/components/BotComment";
import { TimelineEvent } from "@/features/run/components/TimelineEvent";
import type { AgentRun } from "@/features/run/hooks/useAgentRun";
import type { TimelineItem } from "@/features/run/lib/buildTimeline";
import { categoryLabel, NODE_LABEL } from "@/features/run/lib/labels";

type ConversationProps = { run: AgentRun; items: TimelineItem[] };

/** ציר הזמן של הריצה בסגנון שיחה ב-Pull Request, ובסופו מה שקורה עכשיו (עבודה, אבחון או שאלה אלייך). */
export function Conversation({ run, items }: ConversationProps) {
  const { values, phase, approval, currentNode } = run;
  const finished = phase === "succeeded" || phase === "failed";

  return (
    <div className="relative space-y-5 before:absolute before:inset-y-2 before:start-[15px] before:w-0.5 before:bg-line">
      {items.map((item, index) => (
        <TimelineRow key={index} item={item} />
      ))}

      {!finished && values.diagnosis && approval?.kind !== "sensitive_fix" && (
        <BotComment title={<>אבחון נוכחי <Badge tone="pink">{categoryLabel(values.diagnosis.category)}</Badge></>}>
          <p className="font-medium text-ink"><RichText text={values.diagnosis.summary} /></p>
          <p className="mt-1 text-sm text-muted"><RichText text={values.diagnosis.root_cause} /></p>
        </BotComment>
      )}

      {phase === "running" && (
        <TimelineEvent tone="work">
          RepoRunner עובד: <b className="font-semibold text-ink">{currentNode ? (NODE_LABEL[currentNode] ?? currentNode) : "מתחיל"}</b>…
        </TimelineEvent>
      )}

      {phase === "waiting" && approval && <ApprovalCard request={approval} onAnswer={run.answer} />}
    </div>
  );
}

function TimelineRow({ item }: { item: TimelineItem }) {
  if (item.kind === "attempt") return <AttemptCard attempt={item.attempt} />;
  if (item.kind === "event") {
    return (
      <TimelineEvent tone={item.tone} code={item.code}>
        {item.text}
      </TimelineEvent>
    );
  }
  return (
    <BotComment title="התחיל את הריצה">
      {item.profile ? (
        <p>
          זיהיתי פרויקט Python <code>{item.profile.python_version}</code>
          {item.profile.deps_file && <> עם <code>{item.profile.deps_file}</code></>}
          {item.profile.entrypoint && <>, נקודת כניסה <code>{item.profile.entrypoint}</code></>}.
          {item.profile.run_command && <> הפקודה להרצה: <code>{item.profile.run_command}</code>.</>}
        </p>
      ) : (
        <p>משכפל ומנתח את הפרויקט…</p>
      )}
      {item.skipped.length > 0 && (
        <p className="mt-3 text-sm text-muted">
          לא הועתקו לקונטיינר: {item.skipped.map((name) => <code key={name} className="mx-0.5">{name}</code>)}. סביבות, היסטוריית git
          ומפתחות לא עוברים לקוד שרץ בקונטיינר. אם הפרויקט צריך מפתח, הסוכן יבקש אותו ממך.
        </p>
      )}
      {item.plan.length > 0 && (
        <ol className="mt-3 space-y-1.5 text-sm">
          {item.plan.filter((step) => !step.is_fix).map((step) => (
            <li key={step.command} className="flex items-baseline gap-2">
              <span className="text-muted">{step.purpose}:</span>
              <code className="rounded-md bg-inset px-1.5 py-0.5 text-xs text-ink-2">{step.command}</code>
            </li>
          ))}
        </ol>
      )}
    </BotComment>
  );
}
