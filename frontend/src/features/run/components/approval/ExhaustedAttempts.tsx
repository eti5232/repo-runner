import { Button } from "@/components/ui/Button";
import type { ApprovalAnswer, ApprovalRequest } from "@/types/agent";

type Request = Extract<ApprovalRequest, { kind: "attempts_exhausted" }>;
type Props = { request: Request; onAnswer: (answer: ApprovalAnswer) => void };

/** נגמרו הניסיונות: אפשר לתת לסוכן עוד, או לעצור ולקבל דוח. */
export function ExhaustedAttempts({ request, onAnswer }: Props) {
  return (
    <div className="space-y-4">
      <p className="text-[15px] text-ink-2">
        הסוכן ניסה <b className="text-ink">{request.attempts}</b> תיקונים ועדיין לא הצליח להריץ את הפרויקט. אפשר לתת לו עוד
        ניסיונות, או לעצור ולקבל דוח של מה שנמצא.
      </p>
      <div className="flex flex-wrap items-center gap-2.5 border-t border-line pt-4">
        <Button variant="primary" onClick={() => onAnswer({ action: "continue" })}>
          תן עוד ניסיונות
        </Button>
        <Button variant="danger" onClick={() => onAnswer({ action: "stop" })}>
          עצור וקבל דוח
        </Button>
      </div>
    </div>
  );
}
