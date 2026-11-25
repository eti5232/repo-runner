/** שם הריפו לתצוגה: owner/repo מקישור GitHub, או שם התיקייה מנתיב מקומי. */
export function repoNameFromSource(source: string | undefined): string {
  if (!source) return "פרויקט חדש";
  const github = source.match(/github\.com[/:]([^/\s]+)\/([^/\s#?]+?)(?:\.git)?(?:[/#?].*)?$/i);
  if (github) return `${github[1]}/${github[2]}`;
  const parts = source.replace(/[\\/]+$/, "").split(/[\\/]/);
  return parts[parts.length - 1] || source;
}

const rtf = new Intl.RelativeTimeFormat("he", { numeric: "auto" });

/** "לפני 3 דקות" מתוך תאריך ISO. */
export function relativeTime(iso: string | undefined): string {
  if (!iso) return "";
  const seconds = Math.round((new Date(iso).getTime() - Date.now()) / 1000);
  const units: [Intl.RelativeTimeFormatUnit, number][] = [
    ["day", 86400],
    ["hour", 3600],
    ["minute", 60],
  ];
  for (const [unit, size] of units) {
    if (Math.abs(seconds) >= size) return rtf.format(Math.round(seconds / size), unit);
  }
  return "ממש עכשיו";
}

/** שניות לתצוגה קצרה: 0.4 שנ׳ או 2 דק׳. */
export function formatDuration(seconds: number): string {
  if (seconds < 1) return `${Math.round(seconds * 1000)} מ״ש`;
  if (seconds < 60) return `${seconds.toFixed(1)} שנ׳`;
  return `${Math.round(seconds / 60)} דק׳`;
}
