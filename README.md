# ⚡ AgentForge

### Autonomous Software Testing & Repair Agent
**Find. Fix. Verify. Automatically.**

[![Track](https://img.shields.io/badge/Track-Coding_%26_Agentic_Engineering-cyan?style=for-the-badge)](https://nebiusglobalaihackathon.devpost.com/)
[![Model](https://img.shields.io/badge/NVIDIA-Nemotron--3.5--Lightning-76B900?style=for-the-badge&logo=nvidia)](https://studio.nebius.ai/)
[![Inference](https://img.shields.io/badge/Nebius-Token_Factory_API-blue?style=for-the-badge)](https://studio.nebius.ai/)
[![Sandbox](https://img.shields.io/badge/Docker-Isolated_Execution-2496ED?style=for-the-badge&logo=docker)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

---

## 📌 Overview

**AgentForge** is an AI-powered autonomous software engineering agent built for the **Nebius x NVIDIA Global AI Hackathon (Coding & Agentic Engineering Track)**.

Unlike typical AI chatbots that hallucinate unverified code without testing, AgentForge operates on a closed-loop engineering principle:
1. **Inspects** any Python repository and builds an AST manifest.
2. **Executes tests** in an isolated, resource-capped Docker sandbox.
3. **Diagnoses root causes** using **NVIDIA Nemotron open models** via the **Nebius Token Factory inference cluster**.
4. **Synthesizes surgical patches** and applies them *strictly inside the sandbox*.
5. **Re-executes test suites** to independently prove that all tests pass without regressions.
6. **Presents unified git diffs** in an IDE-grade developer mission control interface.

---

## 🏗️ Architecture & Core Agent Loop

```text
Repository (Git Clone or ZIP Upload)
        │
        ▼
Repository Analyzer & Manifest Generator
        │
        ▼
Isolated Docker Sandbox Workspace (512MB RAM, 1.0 CPU, Isolated Network)
        │
        ▼
Baseline Test Execution (pytest) ──▶ Failures Detected (e.g. 5 Passed, 3 Failed)
        │
        ▼
┌────────────────────────────────────────────────────────┐
│     NVIDIA Nemotron-3.5-Lightning (Nebius Token Factory)│
│                 Agent Controller                       │
└──────────────────────────┬─────────────────────────────┘
                           │
       ┌───────────────────┼────────────────────┐
       ▼                   ▼                    ▼
   search_code         read_file           apply_patch
       │                   │                    │
       └───────────────────┼────────────────────┘
                           │
                           ▼
             Sandbox Re-Execution (pytest)
                           │
            ┌──────────────┴──────────────┐
            ▼                             ▼
       Tests Fail?                   All Pass? (8 Passed, 0 Failed)
      (Retry <= 3)                        │
                                          ▼
                         ✓ PATCH VERIFIED BY TESTS
                                          │
                                          ▼
                      Unified Git Diff & Export (.patch)
```

---

## ⚡ NVIDIA & Nebius Integration

AgentForge makes genuine, high-throughput runtime calls to the **Nebius Token Factory inference API**:

* **Target Model**: `nvidia/Nemotron-3_5-Lightning`
* **Inference Endpoint**: `https://api.studio.nebius.ai/v1/chat/completions`
* **Tool Calling Capabilities**: Nemotron iteratively selects and invokes structured JSON tools (`search_code`, `read_file`, `write_file`, `apply_patch`, `run_tests`).
* **Why Nebius Token Factory?**:
  * Low-latency token generation essential for multi-turn agentic loops.
  * Native OpenAI-compatible tool calling.
  * Production stability with high concurrency.

---

## 🛡️ Sandbox Security Architecture

Executing untrusted repository code on a host system is dangerous. AgentForge guarantees total isolation:
* **Disposable Workspaces**: Original repositories on the host are **read-only** and never altered.
* **Isolated Docker Engine**: Containers run as unprivileged users (`agentforge:1000`) with network isolation (`network_mode="none"`), strict memory ceilings (`512MB`), and execution timeouts (`120s`).
* **Path Traversal Guard**: Built-in `SecurityValidator` enforces path boundaries, preventing access to parent directories, `.env` files, or host system paths.

---

## 🖥️ Mission Control Interface (Lovable)

AgentForge avoids generic "AI chatbot" interfaces. It delivers an IDE-grade developer dashboard:
* **Hardware & Runtime Telemetry**: Live status of the Nebius Token Factory connection and Docker engine.
* **Repository Matrix**: Project manifest, language detection, test health counters, and interactive file tree.
* **Monaco-Style Code & Diff Viewer**: Side-by-side unified git diff with syntax coloring and patch download.
* **Live Agent Trace Stream**: Real-time WebSocket feed (`/ws/projects/{id}/trace`) streaming timestamps, tool calls, and model reasoning.
* **Test Run Comparison Drawer**: Before vs. After test run breakdowns straight from container logs.

---

## 🚀 Quickstart & Reproduction Guide

### Prerequisites
* **Python 3.11+**
* **Node.js 18+ & npm**
* **Docker Desktop** (running)
* **Nebius API Key** (from [Nebius AI Studio](https://studio.nebius.ai/))

---

### 1. Clone & Configure
```bash
git clone https://github.com/MOHITPRADHAN35/AgentForge.git
cd AgentForge
cp .env.example backend/.env
```

Edit `backend/.env` with your Nebius credentials:
```env
NEBIUS_API_KEY=your-nebius-api-key-here
NEBIUS_BASE_URL=https://api.studio.nebius.ai/v1
NEMOTRON_MODEL=nvidia/Nemotron-3_5-Lightning
```

---

### 2. Build the Docker Sandbox Image
```bash
docker build -t agentforge-sandbox:latest sandbox/
```

---

### 3. Start the Backend API
```bash
# Windows PowerShell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive API documentation will be available at `http://127.0.0.1:8000/docs`.

---

### 4. Start the Frontend Dashboard
```bash
# In a new terminal
cd frontend
npm install --legacy-peer-deps
npm run dev -- --port 3000
```
Open **http://localhost:3000** in your browser.

---

## 🧪 Testing & Verification

Run the automated backend test suite:
```bash
pytest -v backend/tests/test_backend.py
```

### Verified Test Results
```text
backend/tests/test_backend.py::test_health_endpoint PASSED               [ 12%]
backend/tests/test_backend.py::test_repository_analyzer PASSED           [ 25%]
backend/tests/test_backend.py::test_filesystem_and_patching_tools PASSED [ 37%]
backend/tests/test_backend.py::test_create_and_run_demo_project PASSED   [ 50%]
backend/tests/test_backend.py::test_security_validator_blocks_attacks PASSED [ 62%]
backend/tests/test_backend.py::test_agent_tools_schema PASSED            [ 75%]
backend/tests/test_backend.py::test_zip_repository_extraction PASSED     [ 87%]
backend/tests/test_backend.py::test_project_not_found_handling PASSED    [100%]
======================== 8 passed in 8.47s =========================
```

---

## 📁 Repository Structure

```text
AgentForge/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI entrypoint & routes
│   │   ├── config.py             # Settings & environment variables
│   │   ├── agent/                # Nemotron orchestrator & tools
│   │   ├── sandbox/              # Docker runner & security guards
│   │   ├── nebius/               # Nebius Token Factory OpenAI client
│   │   ├── repository/           # Git/Zip loader & manifest analyzer
│   │   └── database/             # SQLite event & test persistence
│   ├── tests/                    # Automated regression test suite
│   └── requirements.txt
├── frontend/                     # React + Vite + Tailwind Mission Control
│   ├── src/components/           # AgentForgeDashboard & UI components
│   └── package.json
├── sandbox/
│   └── Dockerfile                # Isolated Python execution sandbox
├── demo-repository/              # Reproducible test repo with intentional bugs
├── LICENSE                       # MIT License
├── README.md                     # Documentation
└── .gitignore                    # Secrets & artifact protection
```

---

## 🏆 Hackathon Compliance Checklist

- [x] **Track**: Coding and Agentic Engineering Track
- [x] **NVIDIA Open Source Model**: `nvidia/Nemotron-3_5-Lightning`
- [x] **Nebius Token Factory Runtime Call**: Active inference on `https://api.studio.nebius.ai/v1`
- [x] **Open Source License**: MIT License included and detectable
- [x] **Sandboxed Execution**: Isolated Docker execution container
- [x] **No Hardcoded Secrets**: Protected via `.gitignore` and `.env.example`
- [x] **Reproducible**: Includes `demo-repository` with deterministic bugs

---

## 📄 License
Released under the [MIT License](LICENSE).
