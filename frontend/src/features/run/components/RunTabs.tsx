import { cn } from "@/lib/cn";

export type RunTab = "conversation" | "commands" | "artifacts";

const TABS: { id: RunTab; label: string }[] = [
  { id: "conversation", label: "שיחה" },
  { id: "commands", label: "פקודות" },
  { id: "artifacts", label: "תוצרים" },
];

type RunTabsProps = {
  active: RunTab;
  onChange: (tab: RunTab) => void;
  counts: Record<RunTab, number>;
};

/** לשוניות המסך: שיחה, פקודות ותוצרים. */
export function RunTabs({ active, onChange, counts }: RunTabsProps) {
  return (
    <div role="tablist" className="flex gap-1 border-b border-line">
      {TABS.map((tab) => (
        <button
          key={tab.id}
          role="tab"
          aria-selected={active === tab.id}
          onClick={() => onChange(tab.id)}
          className={cn(
            "-mb-px flex cursor-pointer items-center gap-2 border-b-2 px-4 py-2.5 text-sm transition",
            active === tab.id
              ? "border-orange font-semibold text-ink"
              : "border-transparent text-muted hover:text-ink",
          )}
        >
          {tab.label}
          {counts[tab.id] > 0 && (
            <span className="rounded-full bg-inset px-2 text-xs leading-5 text-muted">{counts[tab.id]}</span>
          )}
        </button>
      ))}
    </div>
  );
}
