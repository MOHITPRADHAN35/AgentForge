# AgentForge

## Autonomous Software Testing & Repair Agent

> **Find. Fix. Verify. Automatically.**

AgentForge is an AI-powered autonomous software engineering agent that analyzes a software repository, understands its structure, generates and executes tests, diagnoses failures, proposes and applies code patches, and verifies the fixes inside an isolated execution environment.

The project is designed for the **Nebius Hackathon — Coding & Agentic Engineering Track**.

The core intelligence is provided by an **NVIDIA Nemotron open model through Nebius Token Factory**.

---

# 1. Product Goal

Build a working application where a user can provide a Python software repository and AgentForge autonomously:

1. Inspect the repository.
2. Understand its structure.
3. Detect the programming language and testing framework.
4. Analyze existing tests.
5. Generate additional tests where useful.
6. Execute tests inside an isolated sandbox.
7. Analyze failures.
8. Identify probable root causes.
9. Generate a code patch.
10. Apply the patch inside the sandbox.
11. Re-run the relevant tests.
12. Verify whether the repair succeeded.
13. Present the entire reasoning/action process through an agent execution trace.

The application must demonstrate genuine **agentic tool use**, not simply generate a textual answer.

---

# 2. Core Product Principle

AgentForge must follow:

```text
Repository
    ↓
Analyze
    ↓
Plan
    ↓
Execute Tools
    ↓
Observe Results
    ↓
Reason
    ↓
Modify Code
    ↓
Test
    ↓
Verify
```

Do NOT build AgentForge as:

```text
User → LLM → Text Response
```

Build it as:

```text
User
 ↓
AgentForge
 ↓
Nemotron
 ↓
Tool Selection
 ↓
Sandbox Execution
 ↓
Evidence
 ↓
Nemotron Reasoning
 ↓
Patch
 ↓
Verification
```

---

# 3. Hackathon Requirements

AgentForge must satisfy the following requirements:

### Required

* Working software application.
* Coding & Agentic Engineering Track.
* NVIDIA open-source model, preferably Nemotron.
* Runtime use of Nebius Token Factory or Nebius AI Cloud.
* Public source repository.
* Open-source license.
* Complete README.
* Working demo/test deployment.
* Public demonstration video under 3 minutes.
* English documentation and demonstration.
* Application must function as demonstrated.
* Repository must contain sufficient source code/assets/instructions to reproduce the application.
* Clearly document Nebius and NVIDIA model usage.

### Nebius Requirement

The application must make a real runtime inference call to Nebius Token Factory or run appropriate components on Nebius AI Cloud.

Do not fake or mock the Nebius/Nemotron integration in production/demo mode.

The README must clearly explain:

```text
Nebius Token Factory
        ↓
Nemotron
        ↓
Agent reasoning
        ↓
Tool orchestration
        ↓
Sandbox
```

---

# 4. MVP Scope

The first production-ready version should support:

### Language

Python only.

### Test framework

pytest.

### Repository input

Support:

* GitHub repository URL
* ZIP upload

Do not attempt multi-language support during MVP.

---

# 5. Primary User Workflow

## Step 1 — Repository Input

User opens AgentForge.

UI:

```text
AgentForge
Autonomous Software Testing & Repair

Repository URL
[ https://github.com/example/project ]

OR

[ Upload ZIP ]

[ Analyze Repository ]
```

---

## Step 2 — Repository Analysis

AgentForge detects:

```text
Language: Python
Test Framework: pytest
Package Manager: pip
Files: 42
Python modules: 27
Tests: 18
Dependencies: 11
```

The application should create a repository manifest.

Example:

```json
{
  "language": "python",
  "test_framework": "pytest",
  "package_manager": "pip",
  "file_count": 42,
  "test_count": 18
}
```

---

# 6. Agent Architecture

Use a tool-calling agent loop.

Conceptually:

```text
┌──────────────────────────┐
│        Nemotron          │
│     Agent Controller     │
└────────────┬─────────────┘
             │
             ↓
       Tool Selection
             │
    ┌────────┼─────────┐
    ↓        ↓         ↓
 Read      Search     Execute
 File      Code       Tests
    │        │         │
    └────────┼─────────┘
             ↓
        Tool Results
             ↓
          Nemotron
             ↓
       Next Decision
```

The agent should be capable of iterative tool execution.

---

# 7. Required Agent Tools

Implement the following tools.

## `list_files`

Lists repository files.

Example:

```json
{
  "path": "src"
}
```

---

## `read_file`

Reads a repository file.

Arguments:

```json
{
  "path": "src/payments.py"
}
```

---

## `search_code`

Searches for symbols, functions, classes, imports, error messages, etc.

Arguments:

```json
{
  "query": "calculate_discount"
}
```

---

## `write_file`

Creates or modifies a file inside the sandbox workspace.

Arguments:

```json
{
  "path": "tests/test_payments.py",
  "content": "..."
}
```

---

## `run_tests`

Runs pytest inside the sandbox.

Arguments:

```json
{
  "test_path": "tests/test_payments.py"
}
```

Return structured results:

```json
{
  "passed": 12,
  "failed": 2,
  "errors": 0,
  "exit_code": 1,
  "stdout": "...",
  "stderr": "..."
}
```

---

## `get_test_output`

Retrieves detailed information about a failed test.

---

## `apply_patch`

Applies a generated patch.

The patch must be recorded before modification.

---

## `git_diff`

Returns the changes made by AgentForge.

---

## `run_static_analysis`

Optional MVP+ tool.

Can run tools such as:

* ruff
* pylint
* mypy

Only use tools that are safely installed/available.

---

# 8. Sandbox Architecture

This is a critical security component.

Never execute arbitrary user repository code directly inside the main AgentForge backend process.

Use an isolated Docker-based execution environment.

Architecture:

```text
AgentForge Backend
       │
       ↓
Sandbox Manager
       │
       ↓
Docker Container
       │
       ├── Repository
       ├── Dependencies
       ├── pytest
       └── Test execution
```

The sandbox should have:

* CPU limits.
* Memory limits.
* Execution timeout.
* Temporary filesystem.
* No host filesystem access.
* Restricted privileges.
* Controlled network access.
* Automatic cleanup after execution.

Never run containers with unnecessary privileged access.

---

# 9. Agent State Machine

Implement explicit agent states.

```text
IDLE
 ↓
INGESTING
 ↓
ANALYZING
 ↓
PLANNING
 ↓
RUNNING_TESTS
 ↓
ANALYZING_FAILURE
 ↓
GENERATING_PATCH
 ↓
APPLYING_PATCH
 ↓
VERIFYING
 ↓
COMPLETED
```

Failure state:

```text
ANY STATE
   ↓
FAILED
   ↓
RECOVERY / USER REVIEW
```

---

# 10. Repair Loop

AgentForge should support a bounded repair loop.

Example:

```text
Initial tests
     ↓
Failures?
     │
   YES
     ↓
Analyze failure
     ↓
Inspect relevant code
     ↓
Generate patch
     ↓
Apply patch
     ↓
Run tests
     ↓
Passed?
   /   \
 YES    NO
  ↓      ↓
DONE   Retry
```

Maximum automatic repair attempts:

```text
3
```

Do not allow infinite loops.

---

# 11. Test Generation

If existing tests do not cover the suspected failure, Nemotron should be able to generate a regression test.

Example:

```python
def test_calculate_average_empty_list():
    assert calculate_average([]) == 0
```

The test should be executed before and after the patch when possible.

This creates evidence that the patch addresses a reproducible problem.

---

# 12. Patch Safety

AgentForge must never silently modify the user's original repository.

Use a temporary working copy:

```text
Original Repository
        │
        ↓
Temporary Sandbox
        │
        ↓
Agent modifications
        │
        ↓
Verification
        │
        ↓
Git Diff
```

Show the user exactly what changed.

Example:

```diff
- discount = total / quantity
+ discount = total / quantity if quantity > 0 else 0
```

---

# 13. Verification Rules

A patch cannot be marked as verified merely because the LLM says it works.

Verification requires actual execution.

Minimum:

```text
Before patch:
18 passed
3 failed

After patch:
23 passed
0 failed
```

The UI should display:

```text
✓ PATCH VERIFIED
```

only after the sandbox test command successfully exits.

If tests still fail:

```text
⚠ REPAIR NOT VERIFIED
```

---

# 14. Agent Execution Trace

This is a major UI feature.

Display a live trace such as:

```text
AGENT TRACE

✓ Repository loaded
✓ Python project detected
✓ pytest detected

→ Inspecting project structure
→ Reading src/payments.py
→ Reading tests/test_payments.py

→ Running baseline tests

✗ 3 test failures detected

→ Investigating failure #1

→ Root cause candidate:
  calculate_discount()

→ Generating regression test

→ Running regression test

✓ Failure reproduced

→ Generating patch

→ Applying patch

→ Running complete test suite

✓ 23/23 tests passed

✓ Repair verified
```

The trace should update in real time using WebSockets or Server-Sent Events.

---

# 15. UI Requirements

The UI should contain four primary areas.

## A. Repository panel

Shows:

* Repository name
* Language
* Framework
* Number of files
* Number of tests
* Analysis status

---

## B. Agent trace

Shows real-time tool calls and agent actions.

---

## C. Code/diff viewer

Shows:

* Original code
* Modified code
* Git diff
* Generated tests

---

## D. Test results

Display:

```text
BEFORE

18 passed
3 failed

AFTER

23 passed
0 failed
```

Use clear visual states:

```text
PASS
FAIL
RUNNING
WARNING
```

Do not overcomplicate the UI.

---

# 16. Suggested Technology Stack

## Frontend

Recommended:

```text
Next.js / React
TypeScript
Tailwind CSS
Monaco Editor
```

Monaco can provide a VS Code-like code/diff experience.

---

## Backend

```text
Python
FastAPI
Pydantic
```

---

## Agent

```text
Nemotron
Nebius Token Factory
Tool-calling / structured outputs
```

Use the Nebius API through environment variables.

Never hard-code API keys.

---

## Execution

```text
Docker
pytest
Git
```

---

## Storage

MVP:

```text
SQLite
```

Production/demo deployment may use:

```text
PostgreSQL
```

Do not add Redis unless asynchronous job handling actually requires it.

---

# 17. Environment Variables

Create:

```text
.env.example
```

Example:

```env
NEBIUS_API_KEY=
NEBIUS_BASE_URL=
NEMOTRON_MODEL=

DATABASE_URL=

SANDBOX_TIMEOUT_SECONDS=120
SANDBOX_MEMORY_LIMIT=512m
SANDBOX_CPU_LIMIT=1
MAX_REPAIR_ATTEMPTS=3
```

Never commit real credentials.

Add `.env` to `.gitignore`.

---

# 18. Backend API

Implement clean REST endpoints.

### Health

```http
GET /api/health
```

---

### Create project

```http
POST /api/projects
```

---

### Analyze repository

```http
POST /api/projects/{project_id}/analyze
```

---

### Start agent

```http
POST /api/projects/{project_id}/agent/run
```

---

### Get project status

```http
GET /api/projects/{project_id}/status
```

---

### Get execution trace

```http
GET /api/projects/{project_id}/trace
```

---

### Get diff

```http
GET /api/projects/{project_id}/diff
```

---

### Get test results

```http
GET /api/projects/{project_id}/tests
```

---

### Live agent stream

Prefer:

```text
WebSocket
```

or:

```text
Server-Sent Events
```

for real-time agent activity.

---

# 19. Suggested Repository Structure

```text
agentforge/
│
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── docker-compose.yml
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   │
│   │   ├── api/
│   │   │   ├── projects.py
│   │   │   ├── agent.py
│   │   │   ├── tests.py
│   │   │   └── health.py
│   │   │
│   │   ├── agent/
│   │   │   ├── orchestrator.py
│   │   │   ├── state.py
│   │   │   ├── prompts.py
│   │   │   └── tools/
│   │   │       ├── filesystem.py
│   │   │       ├── testing.py
│   │   │       ├── patching.py
│   │   │       └── analysis.py
│   │   │
│   │   ├── sandbox/
│   │   │   ├── manager.py
│   │   │   ├── docker_runner.py
│   │   │   └── security.py
│   │   │
│   │   ├── nebius/
│   │   │   ├── client.py
│   │   │   └── models.py
│   │   │
│   │   ├── repository/
│   │   │   ├── loader.py
│   │   │   ├── analyzer.py
│   │   │   └── manifest.py
│   │   │
│   │   └── database/
│   │       ├── models.py
│   │       └── database.py
│   │
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── hooks/
│   ├── package.json
│   └── Dockerfile
│
├── sandbox/
│   ├── Dockerfile
│   └── scripts/
│
├── demo-repository/
│   ├── src/
│   ├── tests/
│   ├── requirements.txt
│   └── README.md
│
└── docs/
    ├── architecture.md
    ├── security.md
    └── demo.md
```

---

# 20. Demo Repository

Create a dedicated deliberately broken Python project for the hackathon demo.

Example:

```text
demo-repository/
├── src/
│   ├── payments.py
│   ├── users.py
│   ├── orders.py
│   └── inventory.py
│
├── tests/
│   ├── test_payments.py
│   ├── test_users.py
│   └── test_orders.py
│
└── requirements.txt
```

Include approximately 3 realistic bugs.

Examples:

* Division by zero.
* Incorrect boundary condition.
* None/null handling bug.
* Off-by-one error.
* Incorrect business logic.

The bugs must be deterministic and reproducible.

---

# 21. Demo Scenario

The official demonstration should show:

```text
00:00
Open AgentForge

00:10
Provide broken repository

00:20
Repository analysis

00:35
Agent runs baseline tests

00:50
Failures appear

01:00
Nemotron investigates

01:20
Agent generates regression test

01:35
Agent generates patch

01:50
Patch applied in sandbox

02:05
Tests run again

02:20
All tests pass

02:30
Show final diff + agent trace
```

Keep the video under 3 minutes.

---

# 22. Security Requirements

Treat repository code as untrusted.

The sandbox must:

* Never run directly on the host.
* Never expose host credentials.
* Never mount sensitive host directories.
* Never expose the Docker socket to the agent.
* Enforce CPU limits.
* Enforce memory limits.
* Enforce execution timeout.
* Use temporary workspaces.
* Clean containers after execution.
* Restrict network access by default.

The Nemotron agent should not have unrestricted shell access.

Prefer explicit tools:

```text
read_file
write_file
run_tests
apply_patch
git_diff
```

rather than:

```text
run_any_command()
```

If shell execution is required internally, place it behind the sandbox manager and enforce allowlists/resource restrictions.

---

# 23. Agent Prompt Design

The system prompt should establish:

```text
You are AgentForge, an autonomous software testing and repair agent.

Your objective is to identify reproducible software defects and produce
verified repairs.

You have access only to the tools provided by AgentForge.

Never claim that a repair works without executing verification tests.

Before modifying code:
1. Understand the relevant code.
2. Reproduce the failure where possible.
3. Identify the likely root cause.
4. Create or update a regression test where appropriate.
5. Generate the smallest reasonable patch.
6. Apply the patch.
7. Run verification tests.

If verification fails, inspect the new evidence and attempt another repair,
subject to the maximum repair-attempt limit.

Never expose secrets.
Never modify the original user repository directly.
```

---

# 24. Observability

Every agent action should generate a structured event.

Example:

```json
{
  "timestamp": "...",
  "type": "tool_call",
  "tool": "run_tests",
  "arguments": {
    "test_path": "tests/test_payments.py"
  },
  "status": "completed"
}
```

Supported event types:

```text
agent_started
analysis_started
tool_call
tool_result
test_started
test_completed
failure_detected
patch_generated
patch_applied
verification_started
verification_completed
agent_completed
agent_failed
```

This powers the Agent Trace UI.

---

# 25. Logging

Use structured logging.

Never log:

* API keys
* Authentication tokens
* User secrets
* Environment secrets

Logs should contain enough information to diagnose agent failures.

---

# 26. Testing Requirements

AgentForge itself must have tests.

Minimum:

### Backend unit tests

Test:

* Repository analyzer
* Patch parser
* Test-result parser
* Agent state machine
* Sandbox manager
* Nebius client
* API endpoints

### Integration tests

At least one complete flow:

```text
Repository
 ↓
Agent
 ↓
Test
 ↓
Failure
 ↓
Patch
 ↓
Verification
```

### Security tests

Verify:

* Sandbox timeout works.
* Memory limits work.
* Containers are cleaned up.
* Host files cannot be accessed.
* Secrets are not passed into the sandbox.

---

# 27. Failure Handling

Never allow the UI to become stuck.

Possible failures:

```text
Nebius API unavailable
Model timeout
Invalid model response
Repository invalid
Docker unavailable
Dependency installation failure
Test timeout
Patch invalid
Tests remain failing
```

Display clear states:

```text
Agent failed safely.

Reason:
Sandbox test execution timed out.

No changes were applied to the original repository.
```

---

# 28. UX Principle

The user should always understand:

```text
WHAT happened?
WHY did the agent do it?
WHAT changed?
DID the fix work?
```

Do not hide everything behind a chat interface.

AgentForge is an **engineering agent**, not a chatbot.

---

# 29. Hackathon Differentiation

The project should emphasize four capabilities:

### 1. Autonomous

The agent chooses what to inspect and which tools to call.

### 2. Executable

The agent actually runs code.

### 3. Verifiable

The agent must prove the repair through tests.

### 4. Safe

Code executes inside an isolated sandbox.

The central product loop is:

> **Reason → Execute → Observe → Repair → Verify**

---

# 30. Non-Goals for MVP

Do NOT spend initial development time on:

* Supporting every programming language.
* Building a complete IDE.
* Autonomous production deployment.
* Kubernetes orchestration.
* Complex multi-agent swarms.
* Training a custom LLM.
* Building a custom code editor.
* Generating enormous documentation.
* Fully autonomous GitHub PR merging.

First make one workflow extremely reliable.

---

# 31. Development Priority

Implement in this order:

## Phase 1 — Foundation

```text
FastAPI
React
Docker
Nebius client
Project management
```

## Phase 2 — Repository intelligence

```text
Repository ingestion
File tree
Code reading
Python detection
pytest detection
```

## Phase 3 — Agent

```text
Nemotron
Tool definitions
Agent loop
State machine
```

## Phase 4 — Execution

```text
Sandbox
pytest
Structured test results
Timeouts
Resource limits
```

## Phase 5 — Repair

```text
Failure analysis
Regression test
Patch generation
Patch application
Verification
```

## Phase 6 — UI

```text
Agent trace
Test results
Diff viewer
Repository status
```

## Phase 7 — Deployment

```text
Nebius deployment
Production configuration
Health checks
Demo repository
```

## Phase 8 — Hackathon polish

```text
README
Architecture diagram
Security documentation
Demo video
Submission description
```

---

# 32. Definition of Done

AgentForge MVP is complete only when this works reliably:

```text
1. User opens web application.
2. User supplies demo repository.
3. AgentForge analyzes it.
4. Nemotron receives the relevant context.
5. Nemotron selects tools.
6. Tests execute in an isolated sandbox.
7. Failures are detected.
8. Nemotron investigates the failure.
9. A regression test is generated where appropriate.
10. A patch is generated.
11. Patch is applied only inside the sandbox.
12. Tests run again.
13. Passing results are independently verified.
14. Git diff is displayed.
15. Agent trace is displayed.
16. User can see exactly what changed.
17. Original repository remains untouched.
18. Application runs using Nebius/Nemotron.
19. The complete workflow works from a clean installation.
```

---

# 33. Final Product Definition

AgentForge should ultimately feel like:

> **A junior software engineer that can independently reproduce bugs, investigate code, write tests, implement repairs, and prove that the repairs work — without being trusted with direct access to the host system.**

The most important demonstration is:

```text
BROKEN CODE
     ↓
AGENT INVESTIGATES
     ↓
TEST FAILURE
     ↓
ROOT CAUSE
     ↓
REGRESSION TEST
     ↓
PATCH
     ↓
SANDBOX
     ↓
RETEST
     ↓
✓ VERIFIED REPAIR
```

Build this workflow first. Everything else is secondary.
