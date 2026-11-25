import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

/** כרטיס עם מסגרת דקה וצל עדין. */
export function Card({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("rounded-2xl border border-line bg-canvas shadow-card", className)} {...rest} />;
}

type CardHeaderProps = { title: ReactNode; aside?: ReactNode; className?: string };

/** כותרת כרטיס: טקסט בצד אחד ותוכן נלווה בצד השני. */
export function CardHeader({ title, aside, className }: CardHeaderProps) {
  return (
    <div className={cn("flex items-center justify-between gap-3 border-b border-line px-5 py-3", className)}>
      <h3 className="text-[13px] font-semibold uppercase tracking-wide text-muted">{title}</h3>
      {aside}
    </div>
  );
}
