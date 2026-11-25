import { Avatar } from "@/components/ui/Avatar";
import { Badge } from "@/components/ui/Badge";
import { PageContainer } from "@/components/layout/PageContainer";
import { repoNameFromSource } from "@/lib/format";
import type { RunPhase } from "@/types/agent";

/** רצועת הזהות של הפרויקט שהריצה שייכת לו, בסגנון כותרת ריפו ב-GitHub. */
export function RepoBand({ source, phase }: { source: string | undefined; phase: RunPhase }) {
  const name = repoNameFromSource(source);
  const [owner, repo] = name.includes("/") ? name.split("/") : [undefined, name];

  return (
    <section
      className="border-b border-line"
      style={{
        background:
          "radial-gradient(520px 170px at 12% -35%, #d6409f20, transparent), radial-gradient(520px 170px at 38% -45%, #fd8c7322, transparent), radial-gradient(520px 170px at 64% -40%, #f2cc0c26, transparent), radial-gradient(520px 170px at 90% -35%, #2da44e1c, transparent), var(--color-subtle)",
      }}
    >
      <PageContainer className="flex items-center gap-4 py-6">
        <Avatar label={repo.slice(0, 2).toUpperCase()} kind="repo" size={52} />
        <div className="min-w-0">
          <h1 className="ltr flex items-center gap-2 text-left text-2xl font-semibold tracking-tight text-ink">
            {owner && <span className="font-normal text-muted">{owner} /</span>}
            <span className="truncate">{repo}</span>
          </h1>
          <p className="ltr truncate text-left text-sm text-muted">{source}</p>
        </div>
        {phase === "succeeded" && (
          <Badge className="ms-auto" tone="green">
            הפרויקט רץ
          </Badge>
        )}
      </PageContainer>
    </section>
  );
}
