import { createFileRoute } from "@tanstack/react-router";
import { AgentForgeDashboard } from "@/components/AgentForgeDashboard";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "AgentForge — Autonomous Testing & Repair Mission Control" },
      { name: "description", content: "IDE-grade observability and mission control for autonomous software testing and repair." },
      { property: "og:title", content: "AgentForge — Autonomous Testing & Repair Mission Control" },
      { property: "og:description", content: "Observe, verify, and control autonomous software repairs powered by NVIDIA Nemotron." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: AgentForgeDashboard,
});
