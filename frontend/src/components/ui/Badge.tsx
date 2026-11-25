import type { HTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export type Tone = "neutral" | "green" | "yellow" | "red" | "pink" | "orange" | "purple";

const TONES: Record<Tone, string> = {
  neutral: "bg-inset text-muted border-line",
  green: "bg-green-soft text-green-deep border-[#a6e3b4]",
  yellow: "bg-yellow-soft text-yellow-deep border-yellow-line",
  red: "bg-red-soft text-red border-[#f3b0aa]",
  pink: "bg-pink-soft text-pink-deep border-[#f1b3d6]",
  orange: "bg-orange-soft text-orange-deep border-[#fdbfae]",
  purple: "bg-purple-soft text-purple border-[#d3bdf7]",
};

type BadgeProps = HTMLAttributes<HTMLSpanElement> & { tone?: Tone };

/** תגית קטנה בצורת גלולה: לתוויות, מונים וסטטוסים. */
export function Badge({ tone = "neutral", className, ...rest }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 text-xs font-medium leading-5",
        TONES[tone],
        className,
      )}
      {...rest}
    />
  );
}
