import type { HTMLAttributes } from "react";
import { cn } from "@/lib/cn";

/** מרכז את התוכן ברוחב אחיד בכל המסכים. */
export function PageContainer({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("mx-auto w-full max-w-[1240px] px-8", className)} {...rest} />;
}
