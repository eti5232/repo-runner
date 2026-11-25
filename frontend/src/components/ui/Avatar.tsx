import { cn } from "@/lib/cn";

type AvatarProps = {
  label: string;
  kind?: "user" | "bot" | "repo";
  size?: number;
  className?: string;
};

const KINDS = {
  user: "bg-gradient-to-br from-[#ffb36b] to-pink rounded-full",
  bot: "bg-gradient-to-br from-[#2da44e] to-[#196c2e] rounded-full",
  repo: "bg-gradient-to-br from-orange to-pink rounded-2xl",
};

/** עיגול עם אותיות: בוט, משתמשת או ריפו. */
export function Avatar({ label, kind = "user", size = 32, className }: AvatarProps) {
  return (
    <span
      className={cn("inline-grid shrink-0 place-items-center font-bold text-white", KINDS[kind], className)}
      style={{ width: size, height: size, fontSize: size * 0.36 }}
    >
      {label}
    </span>
  );
}
