# AgentForge Mission Control

## Build
- Replace the starter screen with a dense, dark, three-column engineering console and bottom test/terminal drawer.
- Establish the cyber-industrial design system using semantic tokens, Inter for interface text, and JetBrains Mono for code and metrics.
- Add repository health, interactive file navigation, a tabbed code/diff workspace, repair verification status, and expandable agent trace events.
- Add working demo-run sequencing, ingestion dialog, copy/download patch actions, pipeline progress, and collapsible terminal tabs.
- Use the specified local backend when reachable, with a complete in-browser mock fallback when it is offline.

## Technical details
- Keep the experience at `/` in TanStack Start and add route-specific social metadata.
- Implement backend calls and WebSocket handling behind a small typed API layer with safe fallback data.
- Keep the desktop split view responsive by collapsing into stacked panels on narrower screens.
- Verify the current build log and exercise the primary demo flow in the live preview.
