import type { ReactNode } from "react";
import { Icon } from "@/components/ui/Icon";
import { ExhaustedAttempts } from "@/features/run/components/approval/ExhaustedAttempts";
import { SecretForm } from "@/features/run/components/approval/SecretForm";
import { SensitiveFix } from "@/features/run/components/approval/SensitiveFix";
import type { ApprovalAnswer, ApprovalRequest } from "@/types/agent";

type ApprovalCardProps = { request: ApprovalRequest; onAnswer: (answer: ApprovalAnswer) => void };

const TITLE: Record<ApprovalRequest["kind"], string> = {
  sensitive_fix: "נדרש אישור: פעולה רגישה",
  secret_needed: "נדרש סוד כדי להמשיך",
  attempts_exhausted: "הסוכן ניסה הרבה פעמים",
};

/** כרטיס "הסוכן ממתין לך". בוחר את הטופס לפי סוג השאלה שהגרף שאל ב-interrupt. */
export function ApprovalCard({ request, onAnswer }: ApprovalCardProps) {
  return (
    <div className="relative flex animate-rise items-start gap-4">
      <span className="relative z-10 mt-1 grid size-8 shrink-0 place-items-center rounded-full bg-yellow text-ink shadow-[0_0_0_6px_white] animate-ring">
        <Icon name="alert" size={16} strokeWidth={2.8} />
      </span>
      <div className="min-w-0 flex-1 rounded-2xl bg-gradient-to-br from-yellow via-yellow-line to-yellow p-px shadow-[0_18px_40px_-24px_rgb(242_204_12/0.9)]">
        <div className="overflow-hidden rounded-[15px] bg-canvas">
          <div className="border-b border-yellow-line bg-gradient-to-b from-yellow-soft to-canvas px-5 py-4">
            <h3 className="text-[17px] font-semibold text-ink">{TITLE[request.kind]}</h3>
            <p className="mt-0.5 text-sm text-yellow-deep">הסוכן עצר וימשיך רק אחרי שתחליטי.</p>
          </div>
          <Body>{renderForm(request, onAnswer)}</Body>
        </div>
      </div>
    </div>
  );
}

function Body({ children }: { children: ReactNode }) {
  return <div className="p-5">{children}</div>;
}

function renderForm(request: ApprovalRequest, onAnswer: (answer: ApprovalAnswer) => void) {
  switch (request.kind) {
    case "sensitive_fix":
      return <SensitiveFix request={request} onAnswer={onAnswer} />;
    case "secret_needed":
      return <SecretForm request={request} onAnswer={onAnswer} />;
    case "attempts_exhausted":
      return <ExhaustedAttempts request={request} onAnswer={onAnswer} />;
  }
}
