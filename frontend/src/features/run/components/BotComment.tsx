import type { ReactNode } from "react";
import { Avatar } from "@/components/ui/Avatar";
import { Badge } from "@/components/ui/Badge";

type BotCommentProps = { title: ReactNode; children: ReactNode };

/** "תגובה" של הבוט בציר הזמן: אווטר מחוץ לתיבה, כותרת אפורה וגוף לבן, כמו ב-Pull Request. */
export function BotComment({ title, children }: BotCommentProps) {
  return (
    <div className="relative flex animate-rise gap-4">
      <Avatar label="RR" kind="bot" className="relative z-10 shadow-[0_0_0_6px_white]" />
      <div className="min-w-0 flex-1 overflow-hidden rounded-xl border border-line bg-canvas shadow-card">
        <div className="flex items-center gap-2.5 border-b border-line bg-subtle px-4 py-2.5 text-sm text-muted">
          <b className="font-semibold text-ink">RepoRunner</b>
          <Badge>bot</Badge>
          {title}
        </div>
        <div className="p-4">{children}</div>
      </div>
    </div>
  );
}
