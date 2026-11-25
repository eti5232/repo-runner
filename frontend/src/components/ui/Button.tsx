import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

type Variant = "primary" | "secondary" | "danger" | "ghost";
type Size = "sm" | "md" | "lg";

const VARIANTS: Record<Variant, string> = {
  primary:
    "bg-gradient-to-b from-[#2da44e] to-green text-white border-black/10 shadow-[inset_0_1px_0_rgb(255_255_255/0.3),0_2px_8px_-2px_rgb(31_136_61/0.5)] hover:brightness-110",
  secondary: "bg-subtle text-ink border-line hover:bg-inset hover:border-line-strong",
  danger: "bg-canvas text-red border-line hover:bg-red-soft hover:border-[#f3b0aa]",
  ghost: "bg-transparent text-muted border-transparent hover:bg-inset hover:text-ink",
};

const SIZES: Record<Size, string> = {
  sm: "h-8 px-3 text-[13px]",
  md: "h-9 px-4 text-sm",
  lg: "h-11 px-6 text-[15px]",
};

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: Size;
  icon?: ReactNode;
};

export function Button({ variant = "secondary", size = "md", icon, className, children, ...rest }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg border font-semibold transition",
        "cursor-pointer disabled:cursor-not-allowed disabled:opacity-45",
        VARIANTS[variant],
        SIZES[size],
        className,
      )}
      {...rest}
    >
      {icon}
      {children}
    </button>
  );
}
