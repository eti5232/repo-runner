import type { CommandResult } from "@/types/agent";

/** פקודה הצליחה אם יצאה בקוד 0 ובלי חריגת זמן (אותו כלל כמו CommandResult.ok ב-Python, שלא עובר ב-JSON). */
export function commandOk(result: CommandResult): boolean {
  return result.exit_code === 0 && !result.timed_out;
}

/** הפלט המאוחד של פקודה: stdout ואז stderr. */
export function commandOutput(result: CommandResult): string {
  return [result.stdout.trim(), result.stderr.trim()].filter(Boolean).join("\n");
}
