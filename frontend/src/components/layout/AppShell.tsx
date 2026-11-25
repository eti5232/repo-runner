import { Outlet } from "react-router-dom";
import { SiteHeader } from "@/components/layout/SiteHeader";

/** מסגרת משותפת לכל המסכים: כותרת למעלה, והתוכן של המסך הנוכחי מתחתיה. */
export function AppShell() {
  return (
    <div className="min-h-screen">
      <SiteHeader />
      <Outlet />
    </div>
  );
}
