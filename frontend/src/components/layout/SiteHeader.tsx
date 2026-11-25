import { NavLink } from "react-router-dom";
import { Icon } from "@/components/ui/Icon";
import { useServerStatus } from "@/hooks/useServerStatus";
import { cn } from "@/lib/cn";

const LINKS = [
  { to: "/", label: "ריצה חדשה", end: true },
  { to: "/runs", label: "כל הריצות", end: false },
];

/** כותרת האתר: לוגו, ניווט וחיווי חיבור לשרת של הסוכן. */
export function SiteHeader() {
  const online = useServerStatus();

  return (
    <header className="bg-subtle">
      <div className="mx-auto flex h-[60px] max-w-[1240px] items-center gap-6 px-8">
        <NavLink to="/" className="flex items-center gap-2.5 text-[17px] font-bold tracking-tight text-ink no-underline">
          <span className="grid size-8 place-items-center rounded-[9px] bg-gradient-to-br from-[#2ea043] to-[#196c2e] shadow-[inset_0_1px_0_rgb(255_255_255/0.4),0_4px_14px_rgb(35_134_54/0.35)]">
            <span className="size-3 rotate-[25deg] rounded-full border-[2.6px] border-white border-s-transparent" />
          </span>
          RepoRunner
        </NavLink>

        <nav className="flex gap-1">
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) =>
                cn(
                  "rounded-lg px-3 py-1.5 text-sm font-medium no-underline transition",
                  isActive ? "bg-inset text-ink" : "text-muted hover:bg-inset hover:text-ink",
                )
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="ms-auto flex items-center gap-2 text-[13px] text-muted">
          <Icon name="dot" size={14} className={cn(online ? "text-green" : online === false ? "text-red" : "text-line-strong")} />
          {online === null ? "בודק חיבור…" : online ? "שרת הסוכן פעיל" : "שרת הסוכן לא זמין"}
        </div>
      </div>
    </header>
  );
}
