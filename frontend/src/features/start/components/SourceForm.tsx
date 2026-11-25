import { useState, type FormEvent } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { createRun } from "@/api/runs";
import { Button } from "@/components/ui/Button";
import { Icon } from "@/components/ui/Icon";
import { Spinner } from "@/components/ui/Spinner";
import { PreviewModePicker } from "@/features/start/components/PreviewModePicker";
import type { PreviewMode } from "@/types/agent";

/** שדה הדבקת קישור (או נתיב מקומי) וכפתור הפעלה. יוצר ריצה חדשה בשרת ועובר למסך הריצה. */
export function SourceForm() {
  const navigate = useNavigate();
  // ההרחבה של GitHub פותחת את האתר עם ?source=<קישור הריפו>, והשדה מתמלא מראש
  const [searchParams] = useSearchParams();
  const [source, setSource] = useState(searchParams.get("source") ?? "");
  const [previewMode, setPreviewMode] = useState<PreviewMode>("none");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const value = source.trim();
    if (!value) return;
    setBusy(true);
    setError(null);
    try {
      const threadId = await createRun();
      // המקור עובר במצב הניווט, ומסך הריצה הוא שמפעיל את הסוכן
      navigate(`/runs/${threadId}`, { state: { source: value, previewMode } });
    } catch {
      setError("לא הצלחתי להתחבר לשרת הסוכן. הרץ langgraph dev ונסי שוב.");
      setBusy(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mt-9">
      <div className="flex gap-2 rounded-2xl border border-line bg-canvas p-2 shadow-pop focus-within:border-green">
        <div className="grid w-10 place-items-center text-muted">
          <Icon name="link" size={18} />
        </div>
        <input
          dir="ltr"
          value={source}
          onChange={(event) => setSource(event.target.value)}
          placeholder="https://github.com/user/project"
          aria-label="קישור לפרויקט"
          className="min-w-0 flex-1 bg-transparent text-left font-mono text-[14.5px] text-ink outline-none placeholder:text-muted/70"
        />
        <Button type="submit" variant="primary" size="lg" disabled={busy || !source.trim()}>
          {busy ? <Spinner /> : <Icon name="play" size={15} />}
          הפעל את הסוכן
        </Button>
      </div>
      <PreviewModePicker value={previewMode} onChange={setPreviewMode} />
      {error ? (
        <p className="mt-3 text-sm text-red">{error}</p>
      ) : (
        <p className="mt-3 text-[13px] text-muted">
          קישור ל-GitHub או נתיב לתיקייה במחשב. פעולות רגישות, כמו התקנת חבילות מערכת או שינוי קוד מקור, תמיד יעצרו לאישור שלך.
        </p>
      )}
    </form>
  );
}
