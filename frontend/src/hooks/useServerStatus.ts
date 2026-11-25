import { useEffect, useState } from "react";
import { pingServer } from "@/api/runs";

/** בודק כל כמה שניות אם השרת של הסוכן זמין. null = עדיין לא ידוע. */
export function useServerStatus(intervalMs = 8000): boolean | null {
  const [online, setOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    const check = async () => {
      const ok = await pingServer();
      if (!cancelled) setOnline(ok);
    };
    void check();
    const timer = window.setInterval(check, intervalMs);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [intervalMs]);

  return online;
}
