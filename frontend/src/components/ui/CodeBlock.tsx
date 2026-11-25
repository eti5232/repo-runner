import { cn } from "@/lib/cn";

type CodeBlockProps = {
  title?: string;
  /** שורות שמסומנות כתוספת (ירוק, עם +) כמו ב-diff */
  added?: boolean;
  lines: string[];
  className?: string;
  tone?: "plain" | "error";
};

/** בלוק קוד קריא עם מספרי שורות. added=true מציג את כל השורות כתוספת, בסגנון diff של GitHub. */
export function CodeBlock({ title, lines, added = false, tone = "plain", className }: CodeBlockProps) {
  return (
    <div className={cn("ltr overflow-hidden rounded-xl border border-line bg-canvas text-left text-[12.5px]", className)}>
      {title && (
        <div className="flex justify-between border-b border-line bg-subtle px-3.5 py-1.5 text-xs text-ink">
          <span className="font-mono" dir="auto">{title}</span>
          {added && <span className="text-green">+{lines.length} −0</span>}
        </div>
      )}
      <div className="overflow-x-auto">
        {lines.map((line, index) => (
          <div
            key={`${index}-${line}`}
            className={cn(
              "grid min-w-max grid-cols-[40px_22px_1fr] font-mono leading-[22px]",
              added && "bg-green-soft text-green-deep",
              tone === "error" && "text-red",
            )}
          >
            <span className="select-none pr-2.5 text-right text-muted/70">{index + 1}</span>
            <span className="select-none text-center opacity-70">{added ? "+" : ""}</span>
            <span className="whitespace-pre pr-4">{line || " "}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
