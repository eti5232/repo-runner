import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Icon } from "@/components/ui/Icon";
import { RichText } from "@/components/ui/RichText";
import { RISK_HELP, RISK_LABEL } from "@/features/run/lib/labels";
import type { ApprovalAnswer, ApprovalRequest } from "@/types/agent";

type Request = Extract<ApprovalRequest, { kind: "sensitive_fix" }>;
type Props = { request: Request; onAnswer: (answer: ApprovalAnswer) => void };

/**
 * תיקון שמצריך אישור: מציג את הפקודות והסיבות, ומאפשר לאשר, לערוך, לדחות או לעצור.
 * בעריכה לכל פקודה יש תיבה משלה, כך שפקודה בת כמה שורות (למשל סקריפט) נשארת שלמה, עם ההזחות שלה.
 */
export function SensitiveFix({ request, onAnswer }: Props) {
  const [editing, setEditing] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const [drafts, setDrafts] = useState<string[]>(request.commands);
  const [note, setNote] = useState("");
  // כמה פקודות יכולות להיות מאותו סוג סיכון, ומספיק להציג כל סיבה פעם אחת
  const uniqueRisks = request.risks.filter((risk, index, all) => all.findIndex((other) => other.kind === risk.kind) === index);

  const updateDraft = (index: number, value: string) =>
    setDrafts((current) => current.map((draft, position) => (position === index ? value : draft)));

  const approve = () => {
    // מסננים רק פקודות ריקות לגמרי. לא נוגעים בתוכן: ירידות שורה והזחות חשובות בסקריפט
    const commands = drafts.filter((draft) => draft.trim() !== "");
    onAnswer(editing ? { action: "approve", commands } : { action: "approve" });
  };

  return (
    <div className="space-y-4">
      <p className="text-[15px] leading-relaxed text-ink-2">
        <RichText text={request.explanation} />
      </p>

      {editing ? (
        <div className="space-y-2.5">
          {drafts.map((draft, index) => (
            <label key={index} className="block">
              <span className="mb-1 block text-xs font-medium text-muted">פקודה {index + 1}</span>
              <textarea
                dir="ltr"
                value={draft}
                onChange={(event) => updateDraft(index, event.target.value)}
                rows={Math.max(2, draft.split("\n").length)}
                spellCheck={false}
                className="w-full rounded-xl border border-line-strong bg-subtle p-3 text-left font-mono text-[13px] leading-relaxed outline-none focus:border-green"
              />
            </label>
          ))}
        </div>
      ) : (
        <div className="ltr rounded-xl border border-line bg-subtle p-3.5 text-left font-mono text-[13px] text-ink">
          {request.commands.map((command) => (
            <div key={command} className="flex gap-2">
              <span className="text-yellow-deep">$</span>
              <span className="whitespace-pre-wrap">{command}</span>
            </div>
          ))}
        </div>
      )}

      <div className="rounded-xl border border-yellow-line bg-yellow-soft/60 p-3.5">
        <p className="mb-2 text-[13px] font-semibold text-yellow-deep">למה זה דורש את האישור שלך</p>
        <ul className="space-y-2 text-sm">
          {uniqueRisks.map((risk) => (
            <li key={risk.kind} className="flex gap-2">
              <Icon name="shield" size={14} className="mt-1 shrink-0 text-yellow-deep" />
              <span>
                <b className="font-semibold text-ink">{RISK_LABEL[risk.kind]}.</b>{" "}
                <span className="text-ink-2">{RISK_HELP[risk.kind]}</span>
              </span>
            </li>
          ))}
        </ul>
        <p className="mt-2.5 border-t border-yellow-line pt-2 text-[13px] text-yellow-deep">
          אישור משפיע רק על הקונטיינר, לא על המחשב שלך. דחייה גורמת לסוכן להציע פתרון אחר.
        </p>
      </div>

      {rejecting && (
        <input
          autoFocus
          value={note}
          onChange={(event) => setNote(event.target.value)}
          placeholder="למה לא? (אופציונלי, הסוכן ישתמש בזה להצעה חדשה)"
          className="w-full rounded-xl border border-line-strong bg-canvas px-3.5 py-2.5 text-sm outline-none focus:border-green"
        />
      )}

      <div className="flex flex-wrap items-center gap-2.5 border-t border-line pt-4">
        {rejecting ? (
          <>
            <Button variant="primary" onClick={() => onAnswer({ action: "reject", note: note.trim() || undefined })}>
              שלח דחייה
            </Button>
            <Button onClick={() => setRejecting(false)}>חזרה</Button>
          </>
        ) : (
          <>
            <Button variant="primary" icon={<Icon name="check" size={15} strokeWidth={2.6} />} onClick={approve}>
              {editing ? "אשר את הגרסה שערכתי" : "אשר והמשך"}
            </Button>
            <Button onClick={() => setEditing((value) => !value)}>{editing ? "בטל עריכה" : "ערוך פקודות"}</Button>
            <Button onClick={() => setRejecting(true)}>דחה והצע אחרת</Button>
            <Button variant="danger" className="ms-auto" onClick={() => onAnswer({ action: "stop" })}>
              עצור ריצה
            </Button>
          </>
        )}
      </div>
    </div>
  );
}
