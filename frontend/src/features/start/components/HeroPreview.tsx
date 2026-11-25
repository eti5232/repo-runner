import { Badge } from "@/components/ui/Badge";
import { Icon, type IconName } from "@/components/ui/Icon";
import { cn } from "@/lib/cn";

type Row = { tone: "ok" | "bad" | "wait"; icon: IconName; text: string; code?: string };

const ROWS: Row[] = [
  { tone: "ok", icon: "check", text: "שכפול וניתוח הפרויקט" },
  { tone: "ok", icon: "check", text: "התקנת התלויות" },
  { tone: "bad", icon: "x", text: "ההרצה נכשלה", code: "No module named 'tkinter'" },
  { tone: "wait", icon: "alert", text: "ממתין לאישור שלך", code: "apt-get install -y python3-tk" },
];

const DOT = { ok: "bg-green text-white", bad: "bg-red text-white", wait: "bg-yellow text-ink animate-ring" };

/** איור דקורטיבי של ריצה: מראה למבקרת מה היא תראה, בלי נתונים אמיתיים. */
export function HeroPreview() {
  return (
    <div aria-hidden className="hidden rotate-[-1.5deg] rounded-2xl border border-line bg-canvas p-5 shadow-pop lg:block">
      <div className="mb-4 flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-widest text-muted">דוגמה לריצה</span>
        <Badge tone="yellow">ממתין לאישור</Badge>
      </div>
      <ul className="space-y-3">
        {ROWS.map((row) => (
          <li key={row.text} className="flex items-start gap-3">
            <span className={cn("mt-0.5 grid size-6 shrink-0 place-items-center rounded-full", DOT[row.tone])}>
              <Icon name={row.icon} size={13} strokeWidth={3} />
            </span>
            <div className="min-w-0">
              <p className="text-sm font-medium text-ink">{row.text}</p>
              {row.code && (
                <code className="mt-1 inline-block rounded-md bg-inset px-2 py-0.5 text-xs text-ink-2">{row.code}</code>
              )}
            </div>
          </li>
        ))}
      </ul>
      <div className="mt-5 flex gap-2 border-t border-line pt-4">
        <span className="rounded-lg bg-green px-3.5 py-1.5 text-[13px] font-semibold text-white">אשר והמשך</span>
        <span className="rounded-lg border border-line bg-subtle px-3.5 py-1.5 text-[13px] font-semibold text-ink">דחה</span>
      </div>
    </div>
  );
}
