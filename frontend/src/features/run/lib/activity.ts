import { commandOk } from "@/lib/command";
import type { RunState } from "@/types/agent";

export type Activity = {
  /** מה הסוכן עושה עכשיו */
  label: string;
  /** למה זה עשוי לקחת זמן */
  hint: string;
  /** אחרי כמה שניות בלי התקדמות מציגים אזהרה */
  slowAfter: number;
};

/**
 * מה קורה עכשיו, לפי ה-State.
 * השרת מעדכן את ה-State רק כשצומת מסתיים, ולכן בזמן שלב ארוך (כמו שכפול) מסיקים אותו ממה שעדיין חסר.
 */
export function currentActivity(values: RunState): Activity {
  if (!values.container) {
    return {
      label: "מכין קונטיינר ומשכפל את הפרויקט",
      hint: "פרויקט גדול או רשת איטית מאריכים את השלב. בפעם הראשונה Docker גם מוריד תמונה של Python.",
      slowAfter: 60,
    };
  }
  if (!values.profile) {
    return { label: "מנתח את הפרויקט", hint: "השלב הזה אמור להיות קצר.", slowAfter: 45 };
  }
  if (values.last_result && !commandOk(values.last_result)) {
    return { label: "מאבחן ומתקן את השגיאה", hint: "המודל קורא את השגיאה וקבצים מהפרויקט.", slowAfter: 90 };
  }
  const next = values.plan?.[values.step_index ?? 0];
  if (next) {
    return { label: `מריץ: ${next.command}`, hint: "התקנת ספריות יכולה לקחת כמה דקות.", slowAfter: 180 };
  }
  return {
    label: "בודק שהפרויקט באמת עובד",
    hint: "פרויקט עם חלון מתקין קודם מסך וירטואלי, וזה יכול לקחת כמה דקות.",
    slowAfter: 180,
  };
}

/** סימן שמשתנה בכל התקדמות. כל עוד הוא זהה, שום שלב לא הסתיים. */
export function progressSignature(values: RunState): string {
  return [
    values.container,
    Boolean(values.profile),
    values.plan?.length,
    values.step_index,
    values.attempts,
    values.last_result?.command,
    Boolean(values.diagnosis),
  ].join("|");
}
