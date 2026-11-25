import { Icon, type IconName } from "@/components/ui/Icon";
import { cn } from "@/lib/cn";
import type { PreviewMode } from "@/types/agent";

const OPTIONS: { value: PreviewMode; icon: IconName; title: string; text: string }[] = [
  { value: "none", icon: "file", title: "רק תוצרים", text: "Dockerfile ודוח, בלי להציג את הפרויקט." },
  { value: "live", icon: "play", title: "תצוגה חיה בדפדפן", text: "הסוכן מריץ את הפרויקט ופותח אותו לך בטאב: אתר, או חלון משחק." },
  { value: "recording", icon: "terminal", title: "הקלטת וידאו", text: "הסוכן מקליט את החלון כמה שניות ומציג לך את הסרטון." },
];

type PreviewModePickerProps = { value: PreviewMode; onChange: (mode: PreviewMode) => void };

/** בחירה מה לעשות בסוף הריצה: כלום, תצוגה חיה או הקלטה. */
export function PreviewModePicker({ value, onChange }: PreviewModePickerProps) {
  return (
    <fieldset className="mt-5">
      <legend className="mb-2 text-[13px] font-medium text-muted">מה לעשות כשהפרויקט רץ?</legend>
      <div className="grid gap-2.5 sm:grid-cols-3">
        {OPTIONS.map((option) => (
          <label
            key={option.value}
            className={cn(
              "flex cursor-pointer flex-col gap-1 rounded-xl border bg-canvas p-3.5 transition",
              value === option.value ? "border-green shadow-[0_0_0_3px_rgb(31_136_61/0.12)]" : "border-line hover:border-line-strong",
            )}
          >
            <input
              type="radio"
              name="preview-mode"
              className="sr-only"
              checked={value === option.value}
              onChange={() => onChange(option.value)}
            />
            <span className="flex items-center gap-2 text-sm font-semibold text-ink">
              <Icon name={option.icon} size={15} className={value === option.value ? "text-green" : "text-muted"} />
              {option.title}
            </span>
            <span className="text-[12.5px] leading-snug text-muted">{option.text}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
