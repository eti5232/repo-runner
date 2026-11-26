/**
 * טיפוסים שמשקפים את הנתונים של הסוכן (reporunner/models.py ו-reporunner/state.py).
 * כל שינוי במודלים של Python צריך להתעדכן גם כאן.
 */

export type RunStatus = "running" | "succeeded" | "failed";

export type DiagnosisCategory =
  | "missing_package"
  | "version_conflict"
  | "missing_system_library"
  | "missing_env_var"
  | "missing_file"
  | "python_version"
  | "code_bug"
  | "other";

export type RiskKind =
  | "system"
  | "remote_script"
  | "secret"
  | "code_change"
  | "custom_source"
  | "outside"
  | "unrecognized"
  | "repeated";

export type Step = {
  command: string;
  purpose: string;
  in_dockerfile: boolean;
  is_fix: boolean;
  as_root: boolean;
};

export type CommandResult = {
  command: string;
  exit_code: number;
  stdout: string;
  stderr: string;
  timed_out: boolean;
  duration_sec: number;
};

export type ProjectProfile = {
  python_version: string;
  deps_file: string | null;
  has_tests: boolean;
  entrypoint: string | null;
  uses_gui: boolean;
  run_command?: string | null;
};

export type Diagnosis = {
  category: DiagnosisCategory;
  summary: string;
  root_cause: string;
  env_var_name?: string | null;
  python_version?: string | null;
};

export type Fix = { commands: string[]; explanation: string };

export type Attempt = {
  number: number;
  failed_command: string;
  error: string;
  category: string;
  fix_commands: string[];
};

export type Risk = { kind: RiskKind; command: string };

export type Approval = {
  kind: "secret_needed" | "sensitive_fix" | "attempts_exhausted";
  action: string;
  detail: string;
};

export type Report = {
  succeeded: boolean;
  summary: string;
  dockerfile: string;
  run_script: string;
  python_version: string;
  env_vars: string[];
  fixes: string[];
  port: number | null;
  help_only: boolean;
  cli_commands: string[];
  cli_help: Record<string, string>;
  run_command: string;
};

/** מה לעשות בסוף הריצה: כלום, תצוגה חיה בדפדפן, או הקלטת וידאו. */
export type PreviewMode = "none" | "live" | "recording";

/** התצוגה שהסוכן הכין: שרת חי (web), חלון חי בדפדפן (desktop), או קובץ וידאו (recording). */
export type Preview = {
  kind: "web" | "desktop" | "recording";
  url: string;
  note: string;
};

/** ה-State של הגרף, כפי שהשרת מחזיר אותו. כל השדות אופציונליים כי הם מתמלאים לאורך הריצה. */
export type RunState = {
  source?: string;
  commit?: string | null;
  container?: string;
  profile?: ProjectProfile;
  skipped?: string[];
  plan?: Step[];
  step_index?: number;
  last_result?: CommandResult;
  diagnosis?: Diagnosis | null;
  proposed_fix?: Fix | null;
  fix_risks?: Risk[];
  approvals?: Approval[];
  attempts?: number;
  attempt_limit?: number;
  attempt_history?: Attempt[];
  preview_mode?: PreviewMode;
  preview?: Preview | null;
  preview_command?: string | null;
  status?: RunStatus;
  report?: Report;
};

/** מה שהסוכן שואל את האדם (המטען של interrupt ב-human_approval). */
export type ApprovalRequest =
  | { kind: "secret_needed"; container: string; env_var: string; summary: string }
  | {
      kind: "sensitive_fix";
      container: string;
      commands: string[];
      explanation: string;
      risks: Risk[];
    }
  | { kind: "attempts_exhausted"; container: string; attempts: number };

/** התשובה של האדם, שנשלחת ל-Command(resume=...). */
export type ApprovalAnswer =
  | { action: "approve"; commands?: string[] }
  | { action: "reject"; note?: string }
  | { action: "provided" }
  | { action: "continue" }
  | { action: "stop" };

/** השלב שבו הריצה נמצאת, כפי שהממשק מציג. */
export type RunPhase = "idle" | "running" | "waiting" | "succeeded" | "failed";
