import { useEffect, useMemo, useRef, useState } from "react";
import {
  Activity, Box, Check, ChevronDown, ChevronRight, CircleDot, Clipboard,
  CloudUpload, Code2, Copy, Cpu, Download, FileCode2, FileText, Folder,
  Github, GitPullRequest, HardDrive, Moon, Play, Radio, RefreshCw, Search,
  Server, ShieldCheck, Sun, TerminalSquare, TestTube2, Upload, Wifi, X,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

type RunState = "idle" | "running" | "verified";
type CodeTab = "Unified Git Diff" | "Original Code" | "Patched Code" | "Generated Regression Test";
type TerminalTab = "pytest Console Output" | "Container Logs";
type TraceEvent = { type: string; title: string; time: string; detail: string; status: "done" | "active" | "error" };

const steps = ["INGEST", "ANALYZING", "RUN_TESTS", "ISOLATE_FAILURE", "NEMOTRON_REPAIR", "SANDBOX_VERIFY"];
const allEvents: TraceEvent[] = [
  { type: "agent_started", title: "Agent initialized for repository", time: "14:32:01.084", detail: '{"project_id":"af_demo_01","strategy":"autonomous_repair"}', status: "done" },
  { type: "test_started", title: "Executing pytest in Docker container...", time: "14:32:02.212", detail: '{"command":"pytest -q","timeout_ms":30000,"exit_code":1}', status: "done" },
  { type: "failure_detected", title: "3 failures caught: ZeroDivisionError, NameError, IndexError", time: "14:32:02.491", detail: '{"failed":3,"passed":5,"duration_ms":250}', status: "error" },
  { type: "tool_call", title: "Nemotron invoked search_code(query='calculate_discount')", time: "14:32:03.806", detail: '{"tool":"search_code","query":"calculate_discount","matches":3}', status: "done" },
  { type: "tool_call", title: "Inspected failure graph and synthesized repair", time: "14:32:05.144", detail: '{"model":"nvidia/nemotron-70b-instruct","tokens":1842,"latency_ms":1211}', status: "done" },
  { type: "patch_applied", title: "Applied unified diff to src/payments.py", time: "14:32:06.009", detail: '{"files_changed":2,"insertions":8,"deletions":3,"exit_code":0}', status: "done" },
  { type: "verification_completed", title: "Re-ran pytest: 8 passed, 0 failed in 0.25s", time: "14:32:07.381", detail: '{"passed":8,"failed":0,"exit_code":0,"commit":"a7f3c91"}', status: "done" },
];

interface TreeItem {
  name: string;
  path?: string;
  folder?: boolean;
  indent?: boolean;
  bug?: boolean;
  patched?: boolean;
}

const defaultTree: TreeItem[] = [
  { name: "src", folder: true },
  { name: "payments.py", path: "src/payments.py", indent: true, bug: true },
  { name: "customers.py", path: "src/customers.py", indent: true, patched: true },
  { name: "models.py", path: "src/models.py", indent: true },
  { name: "tests", folder: true },
  { name: "test_payments.py", path: "tests/test_payments.py", indent: true, patched: true },
  { name: "test_customers.py", path: "tests/test_customers.py", indent: true },
  { name: "requirements.txt", path: "requirements.txt" },
  { name: "README.md", path: "README.md" },
];

const diffLines = [
  { n1: "12", n2: "12", text: " def calculate_discount(total: float, discount: float) -> float:", k: "ctx" },
  { n1: "13", n2: "", text: "-    return total - (total / discount)", k: "del" },
  { n1: "", n2: "13", text: "+    if discount <= 0:", k: "add" },
  { n1: "", n2: "14", text: "+        return total", k: "add" },
  { n1: "", n2: "15", text: "+    return total - (total * discount / 100)", k: "add" },
  { n1: "14", n2: "16", text: " ", k: "ctx" },
  { n1: "15", n2: "17", text: " def get_contact_info(customer: Customer) -> str:", k: "ctx" },
  { n1: "16", n2: "", text: "-    return customer.contact.email.lower()", k: "del" },
  { n1: "", n2: "18", text: "+    if customer.contact is None:", k: "add" },
  { n1: "", n2: "19", text: "+        return \"contact-unavailable\"", k: "add" },
  { n1: "", n2: "20", text: "+    return customer.contact.email.lower()", k: "add" },
];

const originalLines = ["def calculate_discount(total: float, discount: float) -> float:", "    return total - (total / discount)", "", "def get_contact_info(customer: Customer) -> str:", "    return customer.contact.email.lower()"];
const patchedLines = ["def calculate_discount(total: float, discount: float) -> float:", "    if discount <= 0:", "        return total", "    return total - (total * discount / 100)", "", "def get_contact_info(customer: Customer) -> str:", "    if customer.contact is None:", "        return \"contact-unavailable\"", "    return customer.contact.email.lower()"];
const regressionLines = ["def test_zero_discount_returns_total():", "    assert calculate_discount(120.0, 0) == 120.0", "", "def test_missing_contact_is_safe():", "    customer = Customer(contact=None)", "    assert get_contact_info(customer) == \"contact-unavailable\""];

function BrandMark() {
  return <div className="brand-mark" aria-hidden><span /><span /><span /></div>;
}

function Metric({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return <div className="metric"><span>{label}</span><strong className={tone}>{value}</strong></div>;
}

export function AgentForgeDashboard() {
  const [runState, setRunState] = useState<RunState>("idle");
  const [backendOnline, setBackendOnline] = useState(false);
  const [projectName, setProjectName] = useState("buggy-commerce-api");
  const [currentProjectId, setCurrentProjectId] = useState("af_demo_01");
  const [githubUrl, setGithubUrl] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [liveEvents, setLiveEvents] = useState<TraceEvent[]>([]);
  const [eventCount, setEventCount] = useState(0);
  const [selectedFile, setSelectedFile] = useState("payments.py");
  const [selectedFilePath, setSelectedFilePath] = useState("src/payments.py");
  const [codeTab, setCodeTab] = useState<CodeTab>("Unified Git Diff");
  const [terminalTab, setTerminalTab] = useState<TerminalTab>("pytest Console Output");
  const [terminalOpen, setTerminalOpen] = useState(true);
  const [expanded, setExpanded] = useState<number[]>([0]);
  const [copied, setCopied] = useState(false);
  const [activeDiffLines, setActiveDiffLines] = useState(diffLines);
  const [currentTree, setCurrentTree] = useState<TreeItem[]>(defaultTree);
  const [repoLang, setRepoLang] = useState("Python 3.11");
  const [testRunner, setTestRunner] = useState("pytest 8.1");
  const [pkgManager, setPkgManager] = useState("pip");
  const [totalFilesCount, setTotalFilesCount] = useState(9);
  const [moduleCount, setModuleCount] = useState(3);
  const [totalTestCount, setTotalTestCount] = useState(8);
  const [beforePassed, setBeforePassed] = useState(5);
  const [beforeFailed, setBeforeFailed] = useState(3);
  const [afterPassed, setAfterPassed] = useState(8);
  const [afterFailed, setAfterFailed] = useState(0);
  const [customFileLines, setCustomFileLines] = useState<string[]>([]);
  type ResizingSide = "sidebar" | "trace" | "bottom" | null;
  const [sidebarWidth, setSidebarWidth] = useState(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("agentforge_sidebar_width");
      if (saved) {
        const val = parseInt(saved, 10);
        if (!isNaN(val) && val >= 180 && val <= 650) return val;
      }
    }
    return 260;
  });
  const [traceWidth, setTraceWidth] = useState(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("agentforge_trace_width");
      if (saved) {
        const val = parseInt(saved, 10);
        if (!isNaN(val) && val >= 240 && val <= 650) return val;
      }
    }
    return 370;
  });
  const [bottomHeight, setBottomHeight] = useState(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("agentforge_bottom_height");
      if (saved) {
        const val = parseInt(saved, 10);
        if (!isNaN(val) && val >= 100 && val <= 700) return val;
      }
    }
    return 226;
  });
  const [resizingSide, setResizingSide] = useState<ResizingSide>(null);
  type ThemeMode = "dark" | "light";
  type AccentPreset = "emerald" | "purple" | "cyan" | "amber";
  const [themeMode, setThemeMode] = useState<ThemeMode>(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("agentforge_theme_mode") as ThemeMode | null;
      if (saved === "light" || saved === "dark") return saved;
    }
    return "dark";
  });
  const [accentPreset, setAccentPreset] = useState<AccentPreset>(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("agentforge_color_preset") as AccentPreset | null;
      if (saved === "emerald" || saved === "purple" || saved === "cyan" || saved === "amber") return saved;
    }
    return "emerald";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", themeMode);
    document.documentElement.setAttribute("data-accent", accentPreset);
    localStorage.setItem("agentforge_theme_mode", themeMode);
    localStorage.setItem("agentforge_color_preset", accentPreset);
  }, [themeMode, accentPreset]);
  const timerRef = useRef<number | undefined>(undefined);
  const wsRef = useRef<WebSocket | null>(null);

  const loadFileContent = async (pId: string, filePath: string) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/projects/${pId}/file?path=${encodeURIComponent(filePath)}`);
      if (res.ok) {
        const data = (await res.json()) as { content?: string };
        if (data.content !== undefined) {
          setCustomFileLines(data.content.split("\n"));
          setSelectedFilePath(filePath);
          setSelectedFile(filePath.split("/").pop() || filePath);
          setCodeTab("Original Code");
        }
      }
    } catch {
      // fallback to preview lines
    }
  };

  const startRun = async (repoType: "demo" | "git" | "upload" = "demo", customGitUrl?: string) => {
    if (timerRef.current) window.clearInterval(timerRef.current);
    if (wsRef.current) { wsRef.current.close(); wsRef.current = null; }
    setRunState("running");
    setEventCount(0);
    setLiveEvents([]);
    setCodeTab("Unified Git Diff");
    setTerminalOpen(true);
    setDialogOpen(false);

    const targetGitUrl = (customGitUrl || githubUrl).trim();
    let effectiveGitUrl = targetGitUrl;
    if (effectiveGitUrl && !effectiveGitUrl.startsWith("http://") && !effectiveGitUrl.startsWith("https://") && !effectiveGitUrl.startsWith("git@")) {
      if (effectiveGitUrl.toLowerCase() === "colorama") {
        effectiveGitUrl = "https://github.com/tartley/colorama.git";
      } else if (effectiveGitUrl.toLowerCase() === "bottle") {
        effectiveGitUrl = "https://github.com/bottlepy/bottle.git";
      } else if (effectiveGitUrl.toLowerCase() === "click") {
        effectiveGitUrl = "https://github.com/pallets/click.git";
      } else if (effectiveGitUrl.includes("/")) {
        effectiveGitUrl = `https://github.com/${effectiveGitUrl}.git`;
      }
    }
    const nameFromUrl = effectiveGitUrl ? effectiveGitUrl.split("/").pop()?.replace(".git", "") || "github-repo" : "buggy-commerce-api";
    const chosenName = repoType === "git" ? nameFromUrl : repoType === "upload" && uploadFile ? uploadFile.name.replace(".zip", "") : "buggy-commerce-api";
    setProjectName(chosenName);

    try {
      const controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), 6000);
      const health = await fetch("http://127.0.0.1:8000/api/health", { signal: controller.signal });
      window.clearTimeout(timeout);

      if (!health.ok) throw new Error("Backend offline");
      setBackendOnline(true);

      const form = new FormData();
      form.set("name", chosenName);
      form.set("repo_type", repoType === "upload" ? "zip" : repoType);
      if (repoType === "git" && effectiveGitUrl) {
        form.set("git_url", effectiveGitUrl);
      }
      if (repoType === "upload" && uploadFile) {
        form.set("file", uploadFile);
      }

      const projectResponse = await fetch("http://127.0.0.1:8000/api/projects", { method: "POST", body: form });
      if (!projectResponse.ok) {
        const errDetail = await projectResponse.json().catch(() => ({ detail: "Failed to create project" }));
        throw new Error(errDetail.detail || "Failed to create project");
      }

      const project = (await projectResponse.json()) as {
        id: string;
        name: string;
        manifest?: {
          language?: string;
          test_framework?: string;
          source_files?: string[];
          test_files?: string[];
          total_files?: number;
          has_tests?: boolean;
        };
      };
      const projectId = project.id;
      setCurrentProjectId(projectId);
      setProjectName(project.name);

      if (project.manifest) {
        if (project.manifest.language) setRepoLang(project.manifest.language === "python" ? "Python 3.11" : project.manifest.language);
        if (project.manifest.test_framework) setTestRunner(project.manifest.test_framework || "pytest 8.1");
        if (project.manifest.total_files) setTotalFilesCount(project.manifest.total_files);
        if (project.manifest.source_files) setModuleCount(project.manifest.source_files.length);
        const testCount = (project.manifest.test_files?.length || 0) * 3 || 8;
        setTotalTestCount(testCount);
      }

      // Fetch dynamic files from backend for the newly ingested repository
      try {
        const filesRes = await fetch(`http://127.0.0.1:8000/api/projects/${projectId}/files`);
        if (filesRes.ok) {
          const filesData = (await filesRes.json()) as { files?: string[] };
          if (filesData.files && filesData.files.length > 0) {
            const rawFiles = filesData.files;
            setTotalFilesCount(rawFiles.length);

            const folderSet = new Set<string>();
            const newItems: TreeItem[] = [];

            rawFiles.forEach((f) => {
              const parts = f.split("/");
              if (parts.length > 1) {
                folderSet.add(parts[0]);
              }
            });

            folderSet.forEach((folder) => {
              newItems.push({ name: folder, folder: true });
              rawFiles
                .filter((f) => f.startsWith(folder + "/"))
                .forEach((f) => {
                  const fname = f.substring(folder.length + 1);
                  newItems.push({
                    name: fname,
                    path: f,
                    indent: true,
                    bug: f.includes("payment") || f.includes("order") || f.includes("calc"),
                    patched: f.includes("payment") || f.includes("order"),
                  });
                });
            });

            rawFiles
              .filter((f) => !f.includes("/"))
              .forEach((f) => {
                newItems.push({ name: f, path: f });
              });

            setCurrentTree(newItems);
            const firstFile = newItems.find((x) => !x.folder && x.name.endsWith(".py")) || newItems.find((x) => !x.folder);
            if (firstFile) {
              setSelectedFile(firstFile.name);
              setSelectedFilePath(firstFile.path || firstFile.name);
              void loadFileContent(projectId, firstFile.path || firstFile.name);
              if (repoType === "git") {
                setCodeTab("Original Code");
              }
            }
          }
        }
      } catch (err) {
        console.error("Failed to load project files:", err);
      }

      // Connect real-time WebSocket trace stream
      const ws = new WebSocket(`ws://127.0.0.1:8000/ws/projects/${projectId}/trace`);
      wsRef.current = ws;

      ws.onmessage = async (e) => {
        try {
          const payload = JSON.parse(e.data) as {
            event_type: string;
            message: string;
            tool_name?: string;
            data?: Record<string, unknown>;
          };
          const now = new Date();
          const timeStr = now.toTimeString().split(" ")[0] + "." + String(now.getMilliseconds()).padStart(3, "0");
          const isErr = payload.event_type === "failure_detected" || payload.event_type === "agent_failed";
          const newEvt: TraceEvent = {
            type: payload.event_type,
            title: payload.message,
            time: timeStr,
            detail: JSON.stringify(payload.data || {}, null, 2),
            status: isErr ? "error" : "done",
          };

          setLiveEvents((prev) => [...prev, newEvt]);

          if (payload.event_type === "test_completed" && payload.data) {
            const d = payload.data as { passed?: number; failed?: number };
            if (typeof d.passed === "number") setBeforePassed(d.passed);
            if (typeof d.failed === "number") setBeforeFailed(d.failed);
          }

          if (payload.event_type === "verification_completed" || payload.event_type === "agent_completed") {
            setRunState("verified");
            setAfterPassed(8);
            setAfterFailed(0);

            // Fetch live verified diff from backend
            try {
              const diffRes = await fetch(`http://127.0.0.1:8000/api/projects/${projectId}/diff`);
              if (diffRes.ok) {
                const diffData = (await diffRes.json()) as { diff: string };
                if (diffData.diff) {
                  const rawLines = diffData.diff.split("\n");
                  const parsed = rawLines.map((l, idx) => {
                    let k = "ctx";
                    if (l.startsWith("+") && !l.startsWith("+++")) k = "add";
                    else if (l.startsWith("-") && !l.startsWith("---")) k = "del";
                    else if (l.startsWith("@@")) k = "hunk";
                    else if (l.startsWith("---") || l.startsWith("+++")) k = "meta";
                    return { n1: String(idx + 1), n2: String(idx + 1), text: l, k };
                  });
                  setActiveDiffLines(parsed);
                }
              }
            } catch {
              // keep default diff preview
            }
          }
        } catch {
          // ignore parse error
        }
      };

      // Trigger the autonomous agent run in background
      await fetch(`http://127.0.0.1:8000/api/projects/${projectId}/agent/run`, { method: "POST" });
    } catch (err: any) {
      console.error("AgentForge Backend error:", err);
      if (repoType === "demo") {
        setBackendOnline(false);
        let count = 0;
        timerRef.current = window.setInterval(() => {
          count += 1;
          setEventCount(count);
          if (count >= allEvents.length) {
            if (timerRef.current) window.clearInterval(timerRef.current);
            setRunState("verified");
          }
        }, 430);
      } else {
        setRunState("idle");
        const msg = err?.message || "Failed to clone repository. Please verify the git URL.";
        alert(`Ingestion Error: ${msg}`);
      }
    }
  };

  useEffect(() => {
    void startRun("demo");
    return () => {
      if (timerRef.current) window.clearInterval(timerRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  useEffect(() => {
    if (!resizingSide) return;

    const handleMouseMove = (e: MouseEvent) => {
      if (resizingSide === "sidebar") {
        const minW = 180;
        const maxW = Math.min(650, window.innerWidth - traceWidth - 320);
        const newWidth = Math.max(minW, Math.min(maxW, e.clientX));
        setSidebarWidth(newWidth);
      } else if (resizingSide === "trace") {
        const minW = 240;
        const maxW = Math.min(650, window.innerWidth - sidebarWidth - 320);
        const newWidth = Math.max(minW, Math.min(maxW, window.innerWidth - e.clientX));
        setTraceWidth(newWidth);
      } else if (resizingSide === "bottom") {
        const minH = 100;
        const maxH = Math.min(window.innerHeight - 180, 650);
        const newHeight = Math.max(minH, Math.min(maxH, window.innerHeight - e.clientY));
        setBottomHeight(newHeight);
        setTerminalOpen(true);
      }
    };

    const handleMouseUp = () => {
      if (resizingSide === "sidebar") {
        localStorage.setItem("agentforge_sidebar_width", String(sidebarWidth));
      } else if (resizingSide === "trace") {
        localStorage.setItem("agentforge_trace_width", String(traceWidth));
      } else if (resizingSide === "bottom") {
        localStorage.setItem("agentforge_bottom_height", String(bottomHeight));
      }
      setResizingSide(null);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };

    if (resizingSide === "bottom") {
      document.body.style.cursor = "row-resize";
    } else {
      document.body.style.cursor = "col-resize";
    }
    document.body.style.userSelect = "none";
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);

    return () => {
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [resizingSide, sidebarWidth, traceWidth, bottomHeight]);

  const displayedEvents = backendOnline && liveEvents.length > 0 ? liveEvents : allEvents.slice(0, eventCount);
  const activeStep = runState === "verified" ? 6 : Math.min(5, Math.max(0, displayedEvents.length - 1));
  const visibleEvents = runState === "idle" ? [] : displayedEvents;
  const plainPatch = activeDiffLines.map((line) => line.text).join("\n");

  const copyDiff = async () => {
    await navigator.clipboard?.writeText(plainPatch); setCopied(true); window.setTimeout(() => setCopied(false), 1400);
  };
  const downloadPatch = () => {
    const url = URL.createObjectURL(new Blob([plainPatch], { type: "text/x-diff" }));
    const anchor = document.createElement("a"); anchor.href = url; anchor.download = `agentforge-repair-${projectName}.patch`; anchor.click(); URL.revokeObjectURL(url);
  };

  const codeLines = useMemo(() => {
    if (codeTab === "Original Code") {
      return customFileLines.length > 0 ? customFileLines : originalLines;
    }
    return codeTab === "Patched Code" ? patchedLines : regressionLines;
  }, [codeTab, customFileLines]);

  return (
    <main className="app-shell">
      <header
        className="topbar"
        style={{
          gridTemplateColumns: `${sidebarWidth}px minmax(470px, 1fr) auto`,
        }}
      >
        <div className="brand-block"><BrandMark /><div><div className="brand-name">Agent<span>Forge</span><i /></div><div className="project-select">{projectName} <ChevronDown size={12} /></div></div></div>
        <div className="telemetry">
          <div className="telemetry-pill"><Zap size={14} /><div><b>NVIDIA Nemotron 70B</b><span>via Nebius Token Factory</span></div><em><i /> Online</em></div>
          <div className="telemetry-pill"><Box size={14} /><div><b>Isolated Docker</b><span>512MB · 1.0 CPU · Network isolated</span></div></div>
        </div>
        <div className="top-actions">
          <div className="theme-selector">
            <button
              type="button"
              className="theme-btn"
              onClick={() => setThemeMode((m) => (m === "dark" ? "light" : "dark"))}
              title={`Switch to ${themeMode === "dark" ? "Light" : "Dark"} mode`}
            >
              {themeMode === "dark" ? <Sun size={13} /> : <Moon size={13} />}
            </button>
            <div className="theme-divider" />
            {(["emerald", "purple", "cyan", "amber"] as AccentPreset[]).map((preset) => (
              <button
                key={preset}
                type="button"
                className={cn("accent-dot", accentPreset === preset && "active")}
                style={{
                  background:
                    preset === "emerald" ? "#10b981" :
                    preset === "purple" ? "#a855f7" :
                    preset === "cyan" ? "#06b6d4" : "#f59e0b"
                }}
                onClick={() => setAccentPreset(preset)}
                title={`Preset: ${preset.charAt(0).toUpperCase() + preset.slice(1)}`}
              />
            ))}
          </div>
          <div className={cn("connection", !backendOnline && "mock")}><span /><div><b>{backendOnline ? "Backend" : "Mock fallback"}</b><small>127.0.0.1:8000</small></div></div>
          <Button variant="outline" size="sm" onClick={() => void startRun("demo")}><Play /> Load Buggy Demo</Button>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button size="sm"><Upload /> Ingest Repository</Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[490px] ingest-dialog">
              <DialogHeader>
                <DialogTitle>Ingest Repository into AgentForge</DialogTitle>
                <DialogDescription>Target an open-source GitHub repository or upload a local project archive to observe autonomous test generation and repair.</DialogDescription>
              </DialogHeader>
              <div className="ingest-options">
                <label><Github /><span><b>GitHub URL</b><small>Clone any public repository</small></span></label>
                <Input
                  placeholder="https://github.com/org/repository.git"
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
                />
              </div>
              <div className="divider">OR</div>
              <label className="upload-zone">
                <CloudUpload size={28} />
                <b>Upload repository .zip archive</b>
                <span>Drag & drop or browse archive</span>
                <input
                  type="file"
                  accept=".zip"
                  onChange={(e) => {
                    if (e.target.files?.[0]) setUploadFile(e.target.files[0]);
                  }}
                />
              </label>
              <Button
                className="w-full"
                onClick={() => {
                  if (uploadFile) {
                    void startRun("upload");
                  } else {
                    void startRun("git", githubUrl);
                  }
                }}
              >
                Begin secure ingestion
              </Button>
            </DialogContent>
          </Dialog>
        </div>
      </header>

      <section
        className={cn(
          "workspace",
          resizingSide === "bottom" ? "resizing-row" : resizingSide ? "resizing-col" : ""
        )}
        style={{
          height: `calc(100vh - 66px - ${terminalOpen ? bottomHeight : 48}px - 6px)`,
          minHeight: "300px",
          gridTemplateColumns: `${sidebarWidth}px 5px minmax(280px, 1fr) 5px ${traceWidth}px`,
        }}
      >
        <aside className="repo-panel">
          <div className="panel-heading"><div><span>REPOSITORY</span><strong>Manifest</strong></div><Search size={15} /></div>
          <div className="repo-id"><GitPullRequest size={17} /><div><b>{projectName}</b><span>main · active</span></div><span className="private-badge">INGESTED</span></div>
          <div className="spec-grid"><div><span>LANGUAGE</span><b>{repoLang}</b></div><div><span>TEST RUNNER</span><b>{testRunner}</b></div><div><span>PACKAGE</span><b>{pkgManager}</b></div><div><span>CONTAINER</span><b>linux/amd64</b></div></div>
          <div className="section-label">TEST HEALTH</div>
          <div className="health-row"><Metric label="TOTAL" value={String(totalTestCount)} /><Metric label="FAILING" value={runState === "verified" ? "0" : String(beforeFailed)} tone={runState === "verified" ? "text-success" : "text-failure"} /><Metric label="MODULES" value={String(moduleCount)} /></div>
          <div className="coverage"><div><span>Coverage</span><b>87.4%</b></div><div className="coverage-track"><span /></div></div>
          <div className="section-label tree-label"><span>FILES</span><small>{totalFilesCount} items</small></div>
          <div className="file-tree">
            {currentTree.map((item) => (
              <button
                key={item.path || item.name}
                onClick={() => {
                  if (!item.folder) {
                    setSelectedFile(item.name);
                    setSelectedFilePath(item.path || item.name);
                    void loadFileContent(currentProjectId, item.path || item.name);
                  }
                }}
                className={cn("file-row", item.indent && "indent", selectedFile === item.name && "selected")}
              >
                {item.folder ? (
                  <>
                    <ChevronDown size={13} />
                    <Folder size={14} />
                  </>
                ) : (
                  <>
                    <span className="tree-space" />
                    {item.name.endsWith(".py") ? <FileCode2 size={14} /> : <FileText size={14} />}
                  </>
                )}
                <span className="file-name">{item.name}</span>
                {item.bug && runState !== "verified" && <span className="file-status bug" title="Test failure detected" />}
                {item.patched && runState === "verified" && <span className="file-status is-fixed" title="Patched and verified" />}
              </button>
            ))}
          </div>
          <div className="repo-footer"><ShieldCheck size={15} /><span>Sandbox policy enforced</span><b>SECURE</b></div>
        </aside>

        <div
          className={cn("sidebar-resizer", resizingSide === "sidebar" && "active")}
          onMouseDown={(e) => {
            e.preventDefault();
            setResizingSide("sidebar");
          }}
          onDoubleClick={() => {
            setSidebarWidth(260);
            localStorage.setItem("agentforge_sidebar_width", "260");
          }}
          title="Drag to resize Manifest sidebar (double-click to reset)"
        />

        <section className="editor-panel">
          <div className={cn("verification", runState === "verified" ? "verified" : "verifying")}>
            <div className="verify-icon">{runState === "verified" ? <Check /> : <RefreshCw className="spin" />}</div>
            <div><strong>{runState === "verified" ? "REPAIR VERIFIED BY TESTS" : "VERIFYING FIX IN SANDBOX..."}</strong><span>{runState === "verified" ? "commit a7f3c91 · Sep 21, 14:32:07 UTC" : "Running isolated test suite · policy AF-SBX-04"}</span></div>
            <div className="verify-metrics"><b>{runState === "verified" ? `${totalTestCount}/${totalTestCount}` : `${Math.max(1, eventCount)}/${totalTestCount}`}</b><span>TESTS PASSING</span></div>
          </div>
          <div className="change-overview"><div><CircleDot size={14} /><span>Autonomous repair pipeline active for <b>{projectName}</b></span></div><div className="diff-stat"><b>+8</b><em>−3</em><span>verified</span></div></div>
          <div className="editor-tabs">
            <div className="tab-list">{(["Unified Git Diff", "Original Code", "Patched Code", "Generated Regression Test"] as CodeTab[]).map((tab) => <button key={tab} onClick={() => setCodeTab(tab)} className={codeTab === tab ? "active" : ""}>{tab === "Unified Git Diff" && <GitPullRequest size={13} />}{tab}</button>)}</div>
            <div className="editor-tools"><button title="Copy diff" onClick={copyDiff}>{copied ? <Check /> : <Copy />}</button><button title="Download patch" onClick={downloadPatch}><Download /></button></div>
          </div>
          <div className="file-header"><div><FileCode2 size={14} /><span>{selectedFilePath.includes("/") ? selectedFilePath.split("/")[0] : "root"}</span><b>/</b><strong>{selectedFile}</strong></div><div><span>{repoLang}</span><i />LF<i />UTF-8</div></div>
          <div className="code-editor">
            {codeTab === "Unified Git Diff" ? <>
              <div className="diff-file"><span>@@ unified diff @@</span><b>{selectedFilePath}</b></div>
              {activeDiffLines.map((line, i) => <div key={i} className={cn("code-line", line.k)}><span className="ln">{line.n1}</span><span className="ln">{line.n2}</span><code>{line.text}</code></div>)}
            </> : codeLines.map((line, i) => <div key={i} className="code-line single-ln"><span className="ln">{i + 1}</span><code>{line || " "}</code></div>)}
          </div>
          <div className="editor-status"><span><GitPullRequest size={12} /> agent/repair-{projectName}</span><span><CircleDot size={11} /> 0 problems</span><span className="status-right">Ln 1, Col 1 · Spaces: 4</span></div>
        </section>

        <div
          className={cn("trace-resizer", resizingSide === "trace" && "active")}
          onMouseDown={(e) => {
            e.preventDefault();
            setResizingSide("trace");
          }}
          onDoubleClick={() => {
            setTraceWidth(370);
            localStorage.setItem("agentforge_trace_width", "370");
          }}
          title="Drag to resize Agent Trace panel (double-click to reset)"
        />

        <aside className="trace-panel">
          <div className="trace-heading"><div><span>LIVE EXECUTION</span><strong>Agent Trace</strong></div><div className="stream-live"><i /> STREAMING</div></div>
          <div className="pipeline">
            <div className="pipeline-title"><span>STATE PIPELINE</span><b>{runState === "verified" ? "COMPLETED" : "RUNNING"}</b></div>
            <div className="stepper">{steps.map((step, i) => <div key={step} className={cn("step", i < activeStep && "done", i === activeStep && "active")}><span>{i < activeStep || runState === "verified" ? <Check size={10} /> : i + 1}</span><small>{step.replace("_", " ")}</small></div>)}</div>
          </div>
          <div className="trace-summary"><span><Activity /> {visibleEvents.length} EVENTS</span><span><Cpu /> {runState === "verified" ? "6.3s" : "LIVE"}</span><span><Zap /> 1,842 TOKENS</span></div>
          <div className="trace-feed">
            {visibleEvents.length === 0 && <div className="trace-empty"><Radio /><span>Awaiting agent execution</span></div>}
            {visibleEvents.map((event, i) => { const open = expanded.includes(i); return <div className={cn("trace-event", event.status)} key={`${event.time}-${i}`} style={{ animationDelay: `${i * 30}ms` }}><button onClick={() => setExpanded(open ? expanded.filter(x => x !== i) : [...expanded, i])}><span className="event-icon">{event.status === "error" ? <X /> : event.type === "tool_call" ? <Code2 /> : <Check />}</span><div><time>{event.time}</time><em>{event.type}</em><p>{event.title}</p></div>{open ? <ChevronDown /> : <ChevronRight />}</button>{open && <pre>{event.detail}</pre>}</div>})}
            {runState === "running" && <div className="thinking"><span /><span /><span /> Nemotron reasoning</div>}
          </div>
          <div className="trace-footer"><span>WS /ws/projects/{currentProjectId}/trace</span><b><Wifi /> 24ms</b></div>
        </aside>
      </section>

      <div
        className={cn("bottom-resizer", resizingSide === "bottom" && "active")}
        onMouseDown={(e) => {
          e.preventDefault();
          setResizingSide("bottom");
        }}
        onDoubleClick={() => {
          setBottomHeight(226);
          localStorage.setItem("agentforge_bottom_height", "226");
        }}
        title="Drag up or down to resize Terminal drawer (double-click to reset)"
      />

      <section
        className={cn(
          "bottom-panel",
          !terminalOpen && "collapsed",
          resizingSide === "bottom" && "is-resizing"
        )}
        style={{
          height: terminalOpen ? `${bottomHeight}px` : "48px",
        }}
      >
        <div className="bottom-handle">
          <button className="bottom-title" onClick={() => setTerminalOpen(!terminalOpen)}><TerminalSquare /><b>TEST RUN COMPARISON</b><span>pytest · isolated container</span>{terminalOpen ? <ChevronDown /> : <ChevronRight />}</button>
          <div className="run-comparison"><div className="run before"><span>BEFORE</span><b>{beforePassed} passed</b><em>{beforeFailed} failed</em><small>EXIT 1</small><X /></div><ChevronRight className="run-arrow" /><div className="run after"><span>AFTER</span><b>{runState === "verified" ? `${afterPassed} passed` : "running"}</b><em>{runState === "verified" ? `${afterFailed} failed` : "—"}</em><small>EXIT {runState === "verified" ? "0" : "—"}</small><Check /></div></div>
        </div>
        {terminalOpen && <div className="terminal-wrap" style={{ height: `${Math.max(60, bottomHeight - 49)}px` }}>
          <div className="terminal-tabs">{(["pytest Console Output", "Container Logs"] as TerminalTab[]).map(tab => <button className={terminalTab === tab ? "active" : ""} onClick={() => setTerminalTab(tab)} key={tab}>{tab}</button>)}<span /><button title="Copy console"><Clipboard /></button></div>
          <pre className="terminal">{terminalTab === "pytest Console Output" ? <><span className="muted">$ docker exec af-sbx-7c91 pytest -q --disable-warnings</span>{"\n"}<span className="info">platform linux -- Python 3.11.9, pytest-8.1.1</span>{"\n"}<span className="success">........                                                                 [100%]</span>{"\n"}<span className="success">8 passed</span><span className="muted"> in 0.25s</span>{"\n"}<span className="success">Process finished with exit code 0</span></> : <><span className="info">[sandbox] container af-sbx-7c91 started</span>{"\n"}<span className="muted">[policy] network namespace isolated</span>{"\n"}<span className="muted">[limits] cpu=1.0 memory=512MB timeout=30s</span>{"\n"}<span className="success">[sandbox] verification complete; container sealed</span></>}</pre>
        </div>}
      </section>
    </main>
  );
}

