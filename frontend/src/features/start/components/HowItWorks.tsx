import { Icon, type IconName } from "@/components/ui/Icon";

const STEPS: { icon: IconName; title: string; text: string; accent: string }[] = [
  { icon: "terminal", title: "מריץ ומאבחן", text: "מריץ את הפרויקט צעד אחר צעד, וכשמשהו נשבר קורא קבצים כדי להבין למה.", accent: "bg-pink-soft text-pink" },
  { icon: "shield", title: "מתקן בבטיחות", text: "תיקון בטוח רץ לבד. תיקון רגיל ממתין להחלטה שלך, וכללי הבטיחות קבועים בקוד.", accent: "bg-yellow-soft text-yellow-deep" },
  { icon: "box", title: "מחזיר תוצר", text: "Dockerfile שעובד, סקריפט הרצה ודוח של כל מה שהשתנה בדרך.", accent: "bg-green-soft text-green" },
];

/** שלושת הצעדים שמסבירים מה הסוכן עושה. */
export function HowItWorks() {
  return (
    <section>
      <h2 className="mb-5 text-lg font-semibold text-ink">איך זה עובד</h2>
      <div className="grid gap-4 md:grid-cols-3">
        {STEPS.map((step, index) => (
          <div key={step.title} className="rounded-2xl border border-line bg-canvas p-6 shadow-card transition hover:-translate-y-0.5 hover:shadow-pop">
            <div className={`mb-4 grid size-10 place-items-center rounded-xl ${step.accent}`}>
              <Icon name={step.icon} size={20} />
            </div>
            <p className="font-mono text-xs text-muted">0{index + 1}</p>
            <h3 className="mb-1.5 mt-1 text-[17px] font-semibold text-ink">{step.title}</h3>
            <p className="text-sm text-muted">{step.text}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
