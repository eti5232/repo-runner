import { useState, type FormEvent } from "react";
import { sendSecret } from "@/api/secrets";
import { Button } from "@/components/ui/Button";
import { Icon } from "@/components/ui/Icon";
import { Spinner } from "@/components/ui/Spinner";
import type { ApprovalAnswer, ApprovalRequest } from "@/types/agent";

type Request = Extract<ApprovalRequest, { kind: "secret_needed" }>;
type Props = { request: Request; onAnswer: (answer: ApprovalAnswer) => void };

const PLACEHOLDER_VALUE = "dummy-value";

/**
 * הפרויקט צריך משתנה סביבה (סוד). הערך נשלח ישירות לקונטיינר דרך endpoint נפרד,
 * ורק אחרי שנשמר הגרף מקבל {"action": "provided"}. כך הסוד לא נכנס ל-State, ל-checkpointer או ל-LangSmith.
 */
export function SecretForm({ request, onAnswer }: Props) {
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(secret: string) {
    setBusy(true);
    setError(null);
    try {
      await sendSecret(request.container, request.env_var, secret);
      onAnswer({ action: "provided" });
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "שמירת הסוד נכשלה");
      setBusy(false);
    }
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (value) void submit(value);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <p className="text-[15px] text-ink-2">{request.summary}</p>
      <label className="block">
        <span className="mb-1.5 flex items-center gap-1.5 text-[13px] font-medium text-muted">
          <Icon name="lock" size={14} /> הערך של <code className="rounded bg-inset px-1.5">{request.env_var}</code>
        </span>
        <input
          type="password"
          dir="ltr"
          autoComplete="off"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          className="w-full rounded-xl border border-line-strong bg-subtle px-3.5 py-2.5 text-left font-mono text-sm outline-none focus:border-green"
        />
      </label>
      <p className="rounded-xl bg-green-soft px-3.5 py-2.5 text-[13px] text-green-deep">
        הערך נכתב ישירות לקונטיינר בלבד. הוא לא נשמר בזיכרון הסוכן ולא נשלח ל-LangSmith.
      </p>
      {error && <p className="text-sm text-red">{error}</p>}
      <div className="flex flex-wrap items-center gap-2.5 border-t border-line pt-4">
        <Button type="submit" variant="primary" disabled={!value || busy}>
          {busy && <Spinner />} שמור בקונטיינר והמשך
        </Button>
        <Button type="button" disabled={busy} onClick={() => void submit(PLACEHOLDER_VALUE)}>
          המשך עם ערך לדוגמה
        </Button>
        <Button type="button" variant="danger" className="ms-auto" onClick={() => onAnswer({ action: "stop" })}>
          עצור ריצה
        </Button>
      </div>
    </form>
  );
}
