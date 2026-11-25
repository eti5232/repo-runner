import { Link } from "react-router-dom";
import { PageContainer } from "@/components/layout/PageContainer";
import { Button } from "@/components/ui/Button";
import { Icon } from "@/components/ui/Icon";
import { Spinner } from "@/components/ui/Spinner";
import { RunRow } from "@/features/runs/components/RunRow";
import { useRunsList } from "@/features/runs/hooks/useRunsList";

/** רשימת כל הריצות, החדשות ראשונות. */
export function RunsPage() {
  const { runs, loading, error } = useRunsList();

  return (
    <main>
      <PageContainer className="py-10">
        <div className="mb-6 flex items-end justify-between">
          <div>
            <h1 className="text-[28px] font-semibold tracking-tight text-ink">כל הריצות</h1>
            <p className="mt-1 text-muted">כל הריצות נשמרות בשרת, וריצה שעצרה לאישור אפשר להמשיך גם אחרי שסגרת את הדפדפן.</p>
          </div>
          <Link to="/" className="no-underline">
            <Button variant="primary" icon={<Icon name="plus" size={15} />}>
              ריצה חדשה
            </Button>
          </Link>
        </div>

        <div className="overflow-hidden rounded-2xl border border-line bg-canvas shadow-card">
          {loading && (
            <div className="flex items-center gap-3 p-8 text-muted">
              <Spinner /> טוען ריצות…
            </div>
          )}
          {error && <p className="p-8 text-red">לא הצלחתי לטעון את הריצות. ודאי ש-langgraph dev רץ.</p>}
          {!loading && !error && runs.length === 0 && (
            <p className="p-10 text-center text-muted">עוד אין ריצות. הדביקי קישור למסך הבית כדי להתחיל.</p>
          )}
          {runs.map((run) => (
            <RunRow key={run.id} run={run} />
          ))}
        </div>
      </PageContainer>
    </main>
  );
}
