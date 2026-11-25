import { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader } from "@/components/ui/Card";
import { CodeBlock } from "@/components/ui/CodeBlock";
import { Icon } from "@/components/ui/Icon";
import { downloadText } from "@/lib/download";
import type { Report } from "@/types/agent";

/** מה שהסוכן מחזיר בסוף: Dockerfile, סקריפט הרצה ודוח התיקונים. */
export function ArtifactsPanel({ report }: { report: Report | undefined }) {
  if (!report) {
    return (
      <div className="rounded-2xl border border-dashed border-line-strong py-16 text-center">
        <Icon name="box" size={28} className="mx-auto text-line-strong" />
        <p className="mt-3 font-medium text-ink">התוצרים יופיעו כשהריצה תסתיים</p>
        <p className="text-sm text-muted">Dockerfile, סקריפט הרצה ודוח התיקונים.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div
        className={`rounded-2xl border p-5 ${report.succeeded ? "border-[#a6e3b4] bg-green-soft" : "border-[#f3b0aa] bg-red-soft"}`}
      >
        <h3 className={`text-lg font-semibold ${report.succeeded ? "text-green-deep" : "text-red"}`}>
          {report.succeeded ? "הפרויקט רץ" : "הריצה הסתיימה בלי הצלחה"}
        </h3>
        <p className="mt-1 text-sm text-ink-2">{report.summary}</p>
        {report.run_command && (
          <p className="mt-3 text-sm text-ink-2">
            להרצה: <code className="rounded bg-white/70 px-1.5">{report.run_command}</code>
            {report.port && <> · פורט <code className="rounded bg-white/70 px-1.5">{report.port}</code></>}
          </p>
        )}
      </div>

      <FileCard title="Dockerfile" filename="Dockerfile" content={report.dockerfile} />
      <FileCard title="run.sh" filename="run.sh" content={report.run_script} />

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader title="מה השתנה בדרך" aside={<Badge>{report.fixes.length}</Badge>} />
          {report.fixes.length === 0 ? (
            <p className="p-5 text-sm text-muted">הפרויקט רץ בלי שום תיקון.</p>
          ) : (
            <ul className="divide-y divide-line">
              {report.fixes.map((fix) => (
                <li key={fix} className="px-5 py-3 text-sm">{fix}</li>
              ))}
            </ul>
          )}
        </Card>

        <Card>
          <CardHeader title="משתני סביבה נדרשים" aside={<Badge>{report.env_vars.length}</Badge>} />
          {report.env_vars.length === 0 ? (
            <p className="p-5 text-sm text-muted">הפרויקט לא דורש משתני סביבה.</p>
          ) : (
            <div className="flex flex-wrap gap-2 p-5">
              {report.env_vars.map((name) => (
                <code key={name} className="rounded-md bg-inset px-2 py-1 text-xs">{name}</code>
              ))}
            </div>
          )}
        </Card>
      </div>

      <div className="flex flex-wrap gap-3">
        <Button onClick={() => downloadText("REPORT.md", reportMarkdown(report))} icon={<Icon name="download" size={15} />}>
          הורד דוח
        </Button>
        <Button disabled title="בקרוב" icon={<Icon name="branch" size={15} />}>
          פתח Pull request (בקרוב)
        </Button>
      </div>
    </div>
  );
}

function FileCard({ title, filename, content }: { title: string; filename: string; content: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  return (
    <Card>
      <CardHeader
        title={title}
        aside={
          <div className="flex gap-2">
            <Button size="sm" onClick={() => void copy()} icon={<Icon name={copied ? "check" : "copy"} size={14} />}>
              {copied ? "הועתק" : "העתק"}
            </Button>
            <Button size="sm" variant="primary" onClick={() => downloadText(filename, content)} icon={<Icon name="download" size={14} />}>
              הורד
            </Button>
          </div>
        }
      />
      <div className="p-4">
        <CodeBlock lines={content.trimEnd().split("\n")} />
      </div>
    </Card>
  );
}

function reportMarkdown(report: Report): string {
  const fixes = report.fixes.length ? report.fixes.map((fix) => `- ${fix}`).join("\n") : "- לא נדרשו תיקונים";
  const env = report.env_vars.length ? report.env_vars.map((name) => `- ${name}`).join("\n") : "- אין";
  return `# דוח RepoRunner\n\n${report.summary}\n\n## מה תוקן\n${fixes}\n\n## משתני סביבה\n${env}\n\n## הרצה\n\`${report.run_command}\`\n`;
}
