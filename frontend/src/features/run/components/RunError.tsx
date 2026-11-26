import { Link } from "react-router-dom";
import { Button } from "@/components/ui/Button";
import { Icon } from "@/components/ui/Icon";

type RunErrorProps = {
  title: string;
  /** מה קרה ומה לעשות */
  message: string;
};

/** באנר כשהריצה לא תתקדם יותר (שגיאה או עצירה): מסביר למה, ומוביל לריצה חדשה. */
export function RunError({ title, message }: RunErrorProps) {
  return (
    <div role="alert" className="mb-2 mt-6 flex gap-3 rounded-2xl border border-[#f3b0aa] bg-red-soft p-5">
      <Icon name="alert" size={18} className="mt-0.5 shrink-0 text-red" strokeWidth={2.4} />
      <div className="min-w-0">
        <h3 className="font-semibold text-red">{title}</h3>
        <p className="mt-1 whitespace-pre-wrap break-words text-sm text-ink-2">{message}</p>
        <Link to="/" className="mt-3 inline-block no-underline">
          <Button size="sm">ריצה חדשה</Button>
        </Link>
      </div>
    </div>
  );
}
