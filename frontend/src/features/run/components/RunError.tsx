import { Icon } from "@/components/ui/Icon";

type RunErrorProps = { message: string };

/** באנר שגיאה: הריצה נכשלה בשרת. בלעדיו המסך נראה תקוע, כי אין מה להתקדם. */
export function RunError({ message }: RunErrorProps) {
  return (
    <div role="alert" className="mb-6 flex gap-3 rounded-2xl border border-[#f3b0aa] bg-red-soft p-5">
      <Icon name="alert" size={18} className="mt-0.5 shrink-0 text-red" strokeWidth={2.4} />
      <div className="min-w-0">
        <h3 className="font-semibold text-red">הריצה נעצרה בגלל שגיאה</h3>
        <p className="mt-1 text-sm text-ink-2">
          אין כאן משהו שמתקדם. אפשר להתחיל ריצה חדשה (ריצה חדשה, בתפריט למעלה).
        </p>
        <code className="ltr mt-2 block max-h-28 overflow-auto rounded-lg bg-white/70 p-2.5 text-left text-xs">{message}</code>
      </div>
    </div>
  );
}
