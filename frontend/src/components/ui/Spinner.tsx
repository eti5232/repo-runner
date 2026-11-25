import { cn } from "@/lib/cn";

/** עיגול מסתובב לציון טעינה או עבודה בתהליך. */
export function Spinner({ className }: { className?: string }) {
  return (
    <span
      role="status"
      aria-label="טוען"
      className={cn(
        "inline-block size-4 animate-spin rounded-full border-2 border-current border-t-transparent",
        className,
      )}
    />
  );
}
