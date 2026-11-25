import { useEffect, useRef, useState } from "react";
import { recordingUrl, stopPreview } from "@/api/preview";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Icon } from "@/components/ui/Icon";
import type { Preview } from "@/types/agent";

type PreviewCardProps = { preview: Preview; container: string | undefined };

const TITLE = {
  web: "האתר שלך רץ",
  desktop: "החלון של הפרויקט פתוח",
  recording: "הקלטת הפרויקט",
} as const;

/**
 * התצוגה שהסוכן הכין. תצוגה חיה (אתר או חלון) נפתחת אוטומטית בטאב חדש, פעם אחת; אפשר לפתוח שוב ולעצור.
 * הקלטה מוצגת כסרטון בתוך הכרטיס.
 */
export function PreviewCard({ preview, container }: PreviewCardProps) {
  const [stopped, setStopped] = useState(false);
  const opened = useRef(false);
  const live = preview.kind !== "recording";

  // פותחים טאב אוטומטית כשהתצוגה מופיעה. אם הדפדפן חוסם חלון קופץ, הכפתור בכרטיס עדיין עובד
  useEffect(() => {
    if (live && !opened.current) {
      opened.current = true;
      window.open(preview.url, "_blank", "noopener");
    }
  }, [live, preview.url]);

  async function stop() {
    if (container) await stopPreview(container);
    setStopped(true);
  }

  return (
    <section className="mb-6 animate-rise overflow-hidden rounded-2xl border border-line bg-canvas shadow-card">
      <div className="flex flex-wrap items-center gap-3 border-b border-line bg-subtle px-5 py-3.5">
        <Icon name={live ? "play" : "terminal"} size={16} className="text-green" />
        <h3 className="text-[15px] font-semibold text-ink">{TITLE[preview.kind]}</h3>
        {preview.note && <span className="text-[13px] text-muted">{preview.note}</span>}
        {live && (
          <Badge tone={stopped ? "neutral" : "green"} className="ms-auto">
            {stopped ? "נעצר" : "חי"}
          </Badge>
        )}
      </div>

      {preview.kind === "recording" ? (
        <video controls className="w-full bg-ink" src={recordingUrl(preview.url)} />
      ) : (
        <div className="flex flex-wrap items-center gap-3 p-5">
          <code className="ltr min-w-0 flex-1 truncate rounded-lg bg-inset px-3 py-2 text-left text-[13px]">{preview.url}</code>
          <Button
            variant="primary"
            disabled={stopped}
            onClick={() => window.open(preview.url, "_blank", "noopener")}
            icon={<Icon name="link" size={15} />}
          >
            פתח בטאב
          </Button>
          <Button variant="danger" disabled={stopped} onClick={() => void stop()} icon={<Icon name="stop" size={14} />}>
            עצור תצוגה
          </Button>
        </div>
      )}
    </section>
  );
}
