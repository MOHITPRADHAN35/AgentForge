# Devpost Submission Details — AgentForge

> Use the text below to complete your submission form on Devpost for the **Nebius x NVIDIA Global AI Hackathon**.

---

## 1. Project Overview

* **Project Title**: AgentForge — Autonomous Software Testing & Repair Agent
* **Tagline**: Find. Fix. Verify. Automatically. Powered by NVIDIA Nemotron on Nebius Token Factory.
* **Track**: **Coding and Agentic Engineering Track**
* **Repository License**: MIT License
* **Repository URL**: `https://github.com/MOHITPRADHAN35/AgentForge`

---

## 2. Text Description (For Devpost "Project Story" / "About the Project")

### 💡 Inspiration
Today's AI coding assistants act mostly like chatbots: they suggest code changes, but they cannot run tests, cannot prove whether their fixes work, and frequently hallucinate subtle regressions. In enterprise software engineering, running untrusted, AI-generated code directly on production machines introduces severe risks.

We built **AgentForge** to transform AI from a passive code generator into an active, verifiable autonomous software engineer. AgentForge operates on a closed-loop principle: **Observe $\rightarrow$ Diagnose $\rightarrow$ Patch $\rightarrow$ Sandbox Verify**.

---

### ⚙️ What It Does
1. **Repository Ingestion & Analysis**: Ingests Python repositories via GitHub URL or ZIP upload, parsing the AST to build an architectural manifest (modules, pytest suites, dependencies).
2. **Isolated Sandbox Execution**: Provisions a temporary Docker container with restricted CPU, memory (512MB), execution timeouts, and network isolation. Original repositories on the host are strictly read-only.
3. **Automated Defect Reproduction**: Executes `pytest` to capture baseline failures and structured error traces.
4. **NVIDIA Nemotron Reasoning**: Powered by `nvidia/Nemotron-3_5-Lightning` on **Nebius Token Factory**, the agent invokes structured tools (`search_code`, `read_file`, `apply_patch`) to isolate root causes and synthesize minimal surgical fixes.
5. **Independent Verification**: Re-runs the test suite inside the container. AgentForge **never** trusts an LLM's assertion—a repair is only marked verified when pytest exits with code `0`.
6. **Mission Control Observability**: A dense, dark-mode developer dashboard featuring real-time WebSocket trace streaming, live hardware telemetry, and side-by-side Monaco git diff viewers.

---

### 🚀 How We Built It
* **Agent Core**: Python 3.11, FastAPI, Pydantic, and an asynchronous Finite State Machine controller with bounded repair loops (max 3 attempts).
* **NVIDIA & Nebius Integration**: High-throughput OpenAI-compatible inference client communicating directly with `https://api.studio.nebius.ai/v1`, orchestrating `nvidia/Nemotron-3_5-Lightning` through tool calling.
* **Execution Engine**: Docker Python SDK managing disposable containers with path traversal security guards and local subprocess fallback.
* **Frontend Dashboard**: Built with React 19, TypeScript, Tailwind CSS, Monaco Diff Editor, and Lucide icons, receiving real-time agent activity over WebSockets.

---

### 🧗 Challenges We Ran Into
* **Safe Sandbox Mounting**: Ensuring untrusted code executing in the container could never escape or access host files or environment secrets. We solved this with strict POSIX path normalization and Docker volume read/write sandboxing.
* **Reliable Tool Calling**: Directing the LLM to patch source files rather than merely writing duplicate tests. We tailored system prompts to prioritize minimal surgical diffs and verified test execution.

---

### 🏆 Accomplishments That We're Proud Of
* Achieving **sub-second tool calling and verification loops** using Nebius Token Factory.
* Delivering a **100% verified repair** on broken commercial code (going from 5 passed / 3 failed to 8 passed / 0 failed in 0.25s).
* Creating a developer-first mission control UI that eliminates "AI slop" in favor of dense, actionable telemetry.

---

## 3. Feedback on Nebius Token Factory & NVIDIA Technologies

*(Mandatory Submission Requirement per Hackathon Rules)*

### Feedback on Nebius Token Factory:
* **Strengths**: The Token Factory API provided phenomenal inference speeds for `nvidia/Nemotron-3_5-Lightning`. The sub-2-second latency allowed our multi-turn tool-calling loop to feel instantaneous, which is critical for real-time developer agents. The native OpenAI API compatibility made integration straightforward.
* **Suggestions for Improvement**: Enhancing the model catalog documentation with clear, versioned model strings (e.g. distinguishing between instruction-tuned variants) and providing built-in sandbox container APIs directly within Token Factory would accelerate future agent development even further.

### Feedback on NVIDIA Nemotron:
* **Strengths**: Nemotron-3.5 demonstrated exceptional tool-calling discipline and AST comprehension. Unlike smaller models that often break JSON schemas when invoking functions, Nemotron consistently passed valid, clean arguments for `search_code` and `apply_patch`.
* **Strengths in Coding**: It accurately diagnosed complex failure traces (including boundary condition bugs and zero-division edge cases) and synthesized defensive, minimal patches without altering unrelated code.
