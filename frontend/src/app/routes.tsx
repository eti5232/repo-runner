import { createBrowserRouter } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { RunPage } from "@/features/run/RunPage";
import { RunsPage } from "@/features/runs/RunsPage";
import { StartPage } from "@/features/start/StartPage";

/** כל המסכים של האתר. */
export const router = createBrowserRouter([
  {
    element: <AppShell />,
    children: [
      { path: "/", element: <StartPage /> },
      { path: "/runs", element: <RunsPage /> },
      { path: "/runs/:threadId", element: <RunPage /> },
    ],
  },
]);
