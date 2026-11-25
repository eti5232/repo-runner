import { Badge } from "@/components/ui/Badge";
import { CodeBlock } from "@/components/ui/CodeBlock";
import { BotComment } from "@/features/run/components/BotComment";
import { categoryLabel } from "@/features/run/lib/labels";
import type { Attempt } from "@/types/agent";

const ERROR_TAIL_LINES = 8;

/** ניסיון תיקון אחד: מה נכשל, איך אובחן, ואילו פקודות תיקון הופעלו. */
export function AttemptCard({ attempt }: { attempt: Attempt }) {
  const errorLines = attempt.error.trim().split("\n").slice(-ERROR_TAIL_LINES);

  return (
    <BotComment
      title={
        <>
          ניסיון {attempt.number}
          <Badge tone="pink">{categoryLabel(attempt.category)}</Badge>
        </>
      }
    >
      <div className="space-y-4">
        <Row label="שגיאה">
          <CodeBlock lines={errorLines} tone="error" />
        </Row>
        <Row label="תיקון">
          <CodeBlock title="פקודות התיקון" lines={attempt.fix_commands} added />
        </Row>
      </div>
    </BotComment>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid gap-3 sm:grid-cols-[64px_1fr]">
      <span className="pt-1 text-[12.5px] font-medium text-muted">{label}</span>
      <div className="min-w-0">{children}</div>
    </div>
  );
}
