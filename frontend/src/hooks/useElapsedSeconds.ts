import { useEffect, useState } from "react";

/** כמה שניות עברו מאז שהמפתח (key) השתנה. סופר רק כשהוא פעיל. */
export function useElapsedSeconds(key: string, active: boolean): number {
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    setSeconds(0);
    if (!active) return;
    const started = Date.now();
    const timer = window.setInterval(() => setSeconds(Math.floor((Date.now() - started) / 1000)), 1000);
    return () => window.clearInterval(timer);
  }, [key, active]);

  return seconds;
}
