import { useEffect, useRef, useState } from "react";
import { useLocation, useParams, useSearchParams } from "react-router-dom";
import { PageContainer } from "@/components/layout/PageContainer";
import { Spinner } from "@/components/ui/Spinner";
import { AgentPipeline } from "@/features/run/components/AgentPipeline";
import { ArtifactsPanel } from "@/features/run/components/ArtifactsPanel";
import { CommandsPanel } from "@/features/run/components/CommandsPanel";
import { Conversation } from "@/features/run/components/Conversation";
import { RunError } from "@/features/run/components/RunError";
import { RepoBand } from "@/features/run/components/RepoBand";
import { RunProgress } from "@/features/run/components/RunProgress";
import { RunHeader } from "@/features/run/components/RunHeader";
import { RunTabs, type RunTab } from "@/features/run/components/RunTabs";
import { SidePanel } from "@/features/run/components/SidePanel";
import { useAgentRun } from "@/features/run/hooks/useAgentRun";
import { buildTimeline } from "@/features/run/lib/buildTimeline";
import { PreviewCard } from "@/features/run/components/PreviewCard";
import { deriveStages } from "@/lib/pipeline";
import type { PreviewMode } from "@/types/agent";

/** מסך הריצה: מסלול הסוכן, שיחה עם ניסיונות ואישורים, פקודות, תוצרים וסרגל צד. */
export function RunPage() {
  const { threadId = "" } = useParams();
  const location = useLocation();
  const startState = location.state as { source?: string; previewMode?: PreviewMode } | null;
  const startSource = startState?.source;

  const run = useAgentRun(threadId);
  const [searchParams] = useSearchParams();
  const requestedTab = searchParams.get("tab");
  const [tab, setTab] = useState<RunTab>(
    requestedTab === "commands" || requestedTab === "artifacts" ? requestedTab : "conversation",
  );
  const started = useRef(false);

  // ריצה חדשה: ה-thread ריק, ולכן מפעילים את הסוכן פעם אחת עם הקישור שהגיע ממסך ההתחלה
  useEffect(() => {
    if (started.current || !startSource || run.loading || run.values.source) return;
    started.current = true;
    run.start(startSource, startState?.previewMode ?? "none");
  });

  // כשהריצה מצליחה מציגים מיד את התוצרים
  const previousPhase = useRef(run.phase);
  useEffect(() => {
    if (previousPhase.current !== "succeeded" && run.phase === "succeeded" && previousPhase.current === "running") {
      setTab("artifacts");
    }
    previousPhase.current = run.phase;
  }, [run.phase]);

  const pending = run.approval?.kind === "sensitive_fix" ? run.approval.commands.join("; ") : undefined;
  const { items, stats } = buildTimeline(run.values, pending);
  const stages = deriveStages(run.values, run.phase);

  if (run.loading && !run.values.source) {
    return (
      <div className="flex items-center justify-center gap-3 py-32 text-muted">
        <Spinner /> טוען את הריצה…
      </div>
    );
  }

  return (
    <main>
      <RepoBand source={run.values.source ?? startSource} phase={run.phase} />
      <PageContainer className="pb-20 pt-8">
        <RunHeader run={run} />
        {run.failure && <RunError title="הריצה נעצרה בגלל שגיאה" message={run.failure} />}
        {run.stopped && (
          <RunError title="הריצה נעצרה לפני שהסתיימה" message="היא לא תתקדם יותר. אפשר להתחיל ריצה חדשה עם אותו פרויקט." />
        )}
        <RunProgress run={run} />
        <AgentPipeline stages={stages} />

        <div className="mt-8 grid items-start gap-8 lg:grid-cols-[1fr_310px]">
          <div className="min-w-0">
            {run.values.preview && <PreviewCard preview={run.values.preview} container={run.values.container} />}
            <RunTabs
              active={tab}
              onChange={setTab}
              counts={{ conversation: items.length, commands: run.values.plan?.length ?? 0, artifacts: run.values.report ? 1 : 0 }}
            />
            <div className="mt-6">
              {tab === "conversation" && <Conversation run={run} items={items} />}
              {tab === "commands" && <CommandsPanel values={run.values} />}
              {tab === "artifacts" && <ArtifactsPanel report={run.values.report} />}
            </div>
          </div>
          <SidePanel run={run} stats={stats} />
        </div>
      </PageContainer>
    </main>
  );
}
