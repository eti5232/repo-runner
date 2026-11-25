import { useEffect, useState } from "react";
import { listRuns, type RunSummary } from "@/api/runs";

/** טוען את רשימת הריצות מהשרת ומרענן אותה כל כמה שניות (כדי לראות ריצות שמתקדמות). */
export function useRunsList(refreshMs = 6000) {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const next = await listRuns();
        if (!cancelled) {
          setRuns(next);
          setError(false);
        }
      } catch {
        if (!cancelled) setError(true);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    const timer = window.setInterval(load, refreshMs);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [refreshMs]);

  return { runs, loading, error };
}
