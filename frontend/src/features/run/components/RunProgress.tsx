import { Link } from "react-router-dom";
import { Button } from "@/components/ui/Button";
import { Icon } from "@/components/ui/Icon";
import { Spinner } from "@/components/ui/Spinner";
import type { AgentRun } from "@/features/run/hooks/useAgentRun";
import { currentActivity, progressSignature } from "@/features/run/lib/activity";
import { useElapsedSeconds } from "@/hooks/useElapsedSeconds";

/**
 * שורת התקדמות בזמן ריצה: מה קורה וכמה זמן. אם שלב לוקח יותר מהרגיל, מסבירים למה
 * ונותנים דרך לצאת (עצירה או ריצה חדשה), כדי שהמשתמשת לא תישאר מול מסך תקוע.
 */
export function RunProgress({ run }: { run: AgentRun }) {
  const running = run.phase === "running" && !run.failure && !run.stopped;
  const activity = currentActivity(run.values);
  const seconds = useElapsedSeconds(progressSignature(run.values), running);
  if (!running) return null;

  const slow = seconds >= activity.slowAfter;
  const clock = `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;

  return (
    <div role="status" className={`mt-6 rounded-2xl border p-4 ${slow ? "border-yellow-line bg-yellow-soft" : "border-line bg-subtle"}`}>
      <div className="flex items-center gap-3">
        <Spinner className="text-green" />
        <p className="min-w-0 flex-1 truncate text-sm font-semibold text-ink">{activity.label}</p>
        <span className="ltr font-mono text-[13px] text-muted" aria-label="זמן בשלב הנוכחי">
          {clock}
        </span>
      </div>
      <p className="mt-1.5 text-[13px] text-muted">{activity.hint}</p>
      {slow && (
        <div className="mt-3 border-t border-yellow-line pt-3">
          <p className="flex items-center gap-2 text-sm font-semibold text-yellow-deep">
            <Icon name="alert" size={15} /> זה לוקח יותר מהרגיל
          </p>
          <p className="mt-1 text-[13px] text-ink-2">
            אפשר להמתין עוד, או לעצור ולבדוק: שהקישור נכון והריפו ציבורי, ש-Docker Desktop פועל, ושיש חיבור לאינטרנט.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button variant="danger" size="sm" onClick={run.stop} icon={<Icon name="stop" size={13} />}>
              עצור ריצה
            </Button>
            <Link to="/" className="no-underline">
              <Button size="sm">ריצה חדשה</Button>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
