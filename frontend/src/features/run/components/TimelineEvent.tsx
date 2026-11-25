import type { ReactNode } from "react";
import { Icon, type IconName } from "@/components/ui/Icon";
import { Spinner } from "@/components/ui/Spinner";
import { cn } from "@/lib/cn";
import type { EventTone } from "@/features/run/lib/buildTimeline";

const TONE: Record<EventTone | "work", { bg: string; icon: IconName | null }> = {
  ok: { bg: "bg-green text-white", icon: "check" },
  bad: { bg: "bg-red text-white", icon: "x" },
  warn: { bg: "bg-yellow text-ink", icon: "alert" },
  info: { bg: "bg-inset text-muted", icon: "dot" },
  work: { bg: "bg-pink text-white", icon: null },
};

type TimelineEventProps = { tone: EventTone | "work"; children: ReactNode; code?: string };

/** שורת אירוע בציר הזמן: עיגול צבעוני עם אייקון, וטקסט קצר לצידו. */
export function TimelineEvent({ tone, children, code }: TimelineEventProps) {
  const style = TONE[tone];
  return (
    <div className="relative flex animate-rise items-center gap-4 text-sm text-muted">
      <span className={cn("relative z-10 grid size-8 shrink-0 place-items-center rounded-full shadow-[0_0_0_6px_white]", style.bg)}>
        {style.icon ? <Icon name={style.icon} size={15} strokeWidth={2.6} /> : <Spinner className="size-3.5" />}
      </span>
      <span>
        {children}
        {code && (
          <code className="ms-2 rounded-md bg-inset px-1.5 py-0.5 text-xs text-ink-2">{code}</code>
        )}
      </span>
    </div>
  );
}
