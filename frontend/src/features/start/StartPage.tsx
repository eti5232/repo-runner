import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listRuns, type RunSummary } from "@/api/runs";
import { PageContainer } from "@/components/layout/PageContainer";
import { HeroPreview } from "@/features/start/components/HeroPreview";
import { HowItWorks } from "@/features/start/components/HowItWorks";
import { SourceForm } from "@/features/start/components/SourceForm";
import { RunRow } from "@/features/runs/components/RunRow";

/** מסך הבית: הדבקת קישור והפעלת סוכן, ומתחתיו הריצות האחרונות. */
export function StartPage() {
  const [recent, setRecent] = useState<RunSummary[]>([]);

  useEffect(() => {
    listRuns(4)
      .then(setRecent)
      .catch(() => setRecent([]));
  }, []);

  return (
    <main>
      <section className="relative overflow-hidden border-b border-line bg-subtle">
        {/* זוהר עדין רב-צבעי ברקע, נגיעה של ורוד, כתום, צהוב וירוק */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 opacity-90"
          style={{
            background:
              "radial-gradient(520px 260px at 12% 0%, #d6409f1f, transparent), radial-gradient(520px 260px at 40% -10%, #fd8c7326, transparent), radial-gradient(520px 260px at 68% 0%, #f2cc0c26, transparent), radial-gradient(520px 260px at 95% 0%, #1f883d1f, transparent)",
          }}
        />
        <PageContainer className="relative grid items-center gap-12 py-20 lg:grid-cols-[1fr_400px]">
          <div className="max-w-[720px] animate-rise">
            <p className="mb-4 text-right font-mono text-[13px] tracking-widest text-green" dir="ltr">
              AUTONOMOUS ENVIRONMENT REPAIR
            </p>
            <h1 className="text-[54px] font-semibold leading-[1.08] tracking-tight text-ink">
              הפרויקט לא רץ?
              <br />
              <span className="bg-gradient-to-l from-pink via-orange to-yellow bg-clip-text text-transparent">
                הסוכן יגרום לו לרוץ.
              </span>
            </h1>
            <p className="mt-6 max-w-[560px] text-lg text-muted">
              הדביקי קישור לפרויקט Python. הסוכן מריץ אותו בקונטיינר מבודד, מבין מה נשבר, מתקן, ומחזיר Dockerfile שעובד.
            </p>
            <SourceForm />
          </div>
          <HeroPreview />
        </PageContainer>
      </section>

      <PageContainer className="py-14">
        <HowItWorks />

        {recent.length > 0 && (
          <section className="mt-16">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-ink">ריצות אחרונות</h2>
              <Link to="/runs" className="text-sm font-medium text-green no-underline hover:underline">
                לכל הריצות
              </Link>
            </div>
            <div className="overflow-hidden rounded-2xl border border-line bg-canvas shadow-card">
              {recent.map((run) => (
                <RunRow key={run.id} run={run} />
              ))}
            </div>
          </section>
        )}
      </PageContainer>
    </main>
  );
}
