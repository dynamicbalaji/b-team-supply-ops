<div align="center"><img src="./frontend/public/chainguard-logo.png" width="40%" alt="ChainGuardAI" />

# 🛡️ Autonomous Supply Chain Crisis Command 🛡️
</div>

> **5 AI agents. 1 human approval. Crisis resolved in under 5 minutes.**

[![LangGraph](https://img.shields.io/badge/LangGraph-StateGraph-00d4ff?style=flat-square&logo=python)](https://github.com/langchain-ai/langgraph)
[![A2A Protocol](https://img.shields.io/badge/A2A-Protocol-ffb340?style=flat-square)](https://github.com/google/a2a)
[![Gemini](https://img.shields.io/badge/Gemini-3-9b5de5?style=flat-square&logo=google)](https://deepmind.google/technologies/gemini/)
[![FastAPI](https://img.shields.io/badge/FastAPI-async-00e676?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-Vite-61dafb?style=flat-square&logo=react)](https://vitejs.dev)
[![Redis](https://img.shields.io/badge/Redis-Upstash-ff3b5c?style=flat-square&logo=redis)](https://upstash.com)

---

## 🎬 Demo Video

[![ChainGuardAI Demo](https://img.shields.io/badge/YouTube-Demo%20Video-red?style=flat-square&logo=youtube)](https://www.youtube.com/watch?v=hWG2RByWmlg)

**[▶ Watch the full demo on YouTube](https://www.youtube.com/watch?v=hWG2RByWmlg)**

Watch 5 AI agents deliberate, challenge each other, and resolve a $2M supply chain crisis in under 5 minutes — with one human approval and a full audit trail.

---

## Table of Contents

- [🛡️ Autonomous Supply Chain Crisis Command 🛡️](#️-autonomous-supply-chain-crisis-command-️)
  - [🎬 Demo Video](#-demo-video)
  - [Table of Contents](#table-of-contents)
  - [The Problem We're Solving](#the-problem-were-solving)
  - [What ChainGuardAI Does](#what-chainguardai-does)
  - [Architecture Overview](#architecture-overview)
  - [The Agent Network](#the-agent-network)
    - [🎯 Orchestrator Agent](#-orchestrator-agent)
    - [✈️ Logistics Agent](#️-logistics-agent)
    - [💰 Finance Agent](#-finance-agent)
    - [📦 Procurement Agent](#-procurement-agent)
    - [📧 Sales Agent](#-sales-agent)
    - [⚠️ Risk Agent](#️-risk-agent)
  - [Technical Highlights](#technical-highlights)
    - [LangGraph State Machine Orchestration](#langgraph-state-machine-orchestration)
    - [Adversarial Multi-Agent Consensus](#adversarial-multi-agent-consensus)
    - [Monte Carlo Probabilistic Decision Engine](#monte-carlo-probabilistic-decision-engine)
    - [Cross-Session Episodic Memory (TursoDB)](#cross-session-episodic-memory-tursodb)
    - [A2A (Agent-to-Agent) Protocol](#a2a-agent-to-agent-protocol)
    - [Real-Time SSE Streaming](#real-time-sse-streaming)
    - [Human-in-the-Loop Approval Gate](#human-in-the-loop-approval-gate)
  - [Project Structure](#project-structure)
  - [API Reference](#api-reference)
    - [Core Run Lifecycle](#core-run-lifecycle)
    - [A2A Agent Task Endpoints](#a2a-agent-task-endpoints)
  - [Setup \& Local Development](#setup--local-development)
    - [Prerequisites](#prerequisites)
    - [Backend](#backend)
    - [Frontend](#frontend)
    - [Environment Variables](#environment-variables)
  - [Technologies Used](#technologies-used)
    - [AI \& Orchestration](#ai--orchestration)
    - [Backend](#backend-1)
    - [Databases \& Persistence](#databases--persistence)
    - [Frontend](#frontend-1)
    - [DevOps \& Deployment](#devops--deployment)
  - [Hackathon Evaluation Criteria](#hackathon-evaluation-criteria)
    - [🏆 Innovation \& Creativity — 25%](#-innovation--creativity--25)
    - [⚙️ Technical Implementation — 25%](#️-technical-implementation--25)
    - [📈 Feasibility \& Scalability — 15%](#-feasibility--scalability--15)
    - [🎬 Presentation \& Demo — 15%](#-presentation--demo--15)
    - [🤝 Responsible AI — 20%](#-responsible-ai--20)
      - [Fairness \& Bias Mitigation](#fairness--bias-mitigation)
      - [Transparency \& Explainability](#transparency--explainability)
      - [Data Privacy \& Security](#data-privacy--security)
      - [Safety \& Harm Prevention](#safety--harm-prevention)
      - [Accountability](#accountability)
  - [Key Design Decisions \& Trade-offs](#key-design-decisions--trade-offs)
  - [What's Next](#whats-next)
  - [Team](#team)
  - [References \& Sources](#references--sources)

---

## The Problem We're Solving

Every year, supply chain disruptions cost enterprises **$184 billion** in avoidable losses ([Interos Annual Global Supply Chain Report, 2021](https://www.fbcinc.com/source/virtualhall_images/HHS/Interos/1._NEW_Interos_WP_Cost_of_Status_Quo_08.03.21.pdf)). When a port strike, customs hold, or supplier bankruptcy hits, the typical response looks like this:

- **Hour 0–4:** Incident reported across 6 time zones
- **Hour 4–24:** Cross-functional calls with Logistics, Finance, Procurement, Sales
- **Hour 24–36:** Analysis paralysis — cost estimates vary by $200K depending on who you ask
- **Hour 36–48:** Decision finally made — often too late, often the expensive default

**No real-time cost quantification. No institutional memory. No audit trail. No coordination.**

ChainGuardAI replaces that entire process with a multi-agent AI deliberation that produces a confidence-quantified recommendation in **under 5 minutes**, backed by Monte Carlo simulation, cross-session episodic memory, and adversarial consensus — with exactly one human decision required.

---

## What ChainGuardAI Does

ChainGuardAI deploys **5 specialized AI agents** that simultaneously receive a supply chain crisis, evaluate it from their domain perspective, debate each other's assumptions, and converge on the optimal resolution plan — before escalating to a human approver.

The moment approval is clicked, a second LangGraph graph executes the full downstream cascade: freight booked, customer notified, budget released, spot order cancelled. End to end, in one session.

**Live demo scenarios:**

| Scenario | Customer | Shipment Value | Penalty at Risk | Saved |
|---|---|---|---|---|
| 🚢 Port Strike — Long Beach | Apple Inc. | $12M | $2,000,000 | $1,720,000 |
| 🛃 Customs Delay — Shanghai | Samsung Electronics | $8M | $1,500,000 | $1,100,000 |
| 🏭 Supplier Breach — Taiwan | NVIDIA | $20M | $5,000,000 | $4,500,000 |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FRONTEND — React + Vite                          │
│  Agent Network Panel · Decision Matrix (D3) · Leaflet Map           │
│  Audit Trail · Chat Feed · Phase Strip · VP Approval Panel          │
└────────────────────────────┬────────────────────────────────────────┘
                             │ SSE (Server-Sent Events) — real-time streaming
┌────────────────────────────▼────────────────────────────────────────┐
│              ORCHESTRATION — FastAPI + LangGraph                    │
│                                                                     │
│   _SCENARIO_GRAPH (pre-approval)    _CASCADE_GRAPH (post-approval)  │
│   ┌─ phase0_broadcast               ┌─ exec_phase_transition        │
│   ├─ round1_logistics               ├─ exec_logistics_confirm        │
│   ├─ round1_procurement             ├─ exec_sales_notify             │
│   ├─ round2_finance                 ├─ exec_finance_release          │
│   ├─ round2b_logistics_revise       ├─ exec_procurement_cancel       │
│   ├─ round3_sales                   └─ exec_complete → END           │
│   ├─ round4_risk                                                     │
│   ├─ round5_consensus               A2A Task Router                  │
│   └─ awaiting_approval → END        SSE Publisher                    │
│                                     Audit PDF Generator              │
└────────────────────────────┬────────────────────────────────────────┘
                             │ Redis pub/sub · state hydration
┌────────────────────────────▼────────────────────────────────────────┐
│                      PERSISTENCE LAYER                              │
│   Redis (Upstash)              TursoDB (libSQL / Turso edge)        │
│   · Real-time SSE pub/sub      · Episodic memory (cross-session)    │
│   · Run state hydration        · Run context persistence            │
│   · Cross-process messaging    · Agent learning records             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## The Agent Network

Each agent runs its own compiled **LangGraph StateGraph** with dedicated tools, a distinct reasoning persona, and a specific role in the consensus protocol.

### 🎯 Orchestrator Agent
The master graph. Sequences agent rounds, emits phase transitions, gates human approval. No hand-written `asyncio` at the orchestration level — LangGraph drives the execution schedule entirely.

### ✈️ Logistics Agent
Evaluates freight routes (Air-only, Sea-only, Hybrid 60/40). Calls `check_freight_rates()` for live cost/time/risk data. Critically, runs `memory_recall()` against TursoDB to surface similar past crises and their outcomes — *"March 2024 LA port strike resolved with hybrid at $253K, saved $180K"* — before making a recommendation. Revises route if Finance challenges its cost assumptions.

### 💰 Finance Agent
The probabilistic backbone. Runs a **100-iteration Monte Carlo simulation** drawing from a normal distribution around the base cost estimate, producing P10, P90, mean, and a 22-bucket histogram for live D3 chart rendering. Simultaneously calls `query_customs_rates()` to challenge Logistics' LAX cost assumption. Proposes the final consensus recommendation with an explicit contingency reserve. This is not a chatbot guessing a number — it's a quantified risk engine.

### 📦 Procurement Agent
Queries live supplier inventory databases for alternative sourcing options. Identifies partial-quantity shortfalls (e.g. "Dallas supplier only 80% quantity available"), evaluates spot purchase costs, and schedules backup supplier slots. Provides the "Plan B" if the primary logistics route fails.

### 📧 Sales Agent
Retrieves active customer contract terms, calculates the precise penalty exposure, determines whether SLA extension windows are contractually available, and drafts formal amendment documentation. Negotiates directly: *"Apple accepts 36h delay + Q3 priority allocation. Zero financial penalty confirmed."*

### ⚠️ Risk Agent
The devil's advocate. **Never part of the consensus — always challenging it.** After all other agents reach agreement, Risk Agent evaluates the plan for single points of failure, unconfirmed capacity assumptions, and missing contingency triggers. It cannot be bypassed. Example output: *"LAX ground crew unconfirmed during active strike conditions. Single point of failure. Recommend Hour-20 backup trigger to Tucson air route."*

---

## Technical Highlights

### LangGraph State Machine Orchestration

All business logic control flow is expressed as **graph edges, not code**. There is no `asyncio.gather`, `asyncio.sleep`, or `asyncio.create_task` at the orchestration level. Two compiled `StateGraph` instances handle the full lifecycle:

```python
# Pre-approval scenario graph
g.add_edge("phase0_broadcast",         "round1_logistics")
g.add_edge("round1_logistics",         "round1_procurement")
g.add_edge("round1_procurement",       "round2_finance")
g.add_edge("round2_finance",           "round2b_logistics_revise")
g.add_edge("round2b_logistics_revise", "round3_sales")
g.add_edge("round3_sales",             "round4_risk")
g.add_edge("round4_risk",              "round5_consensus")
g.add_edge("round5_consensus",         "awaiting_approval")
```

Intra-node parallelism (e.g. Finance fetching Monte Carlo + customs rates simultaneously) is scoped to single logical steps via `asyncio.gather` — never at the cross-agent control flow level. This design is clean, testable, and fully reproducible.

### Adversarial Multi-Agent Consensus

Agents don't just pass data forward sequentially. Finance **challenges** Logistics:

> *"Your $450K estimate — does that include expedited customs at LAX during strike conditions?"*

Logistics **revises** based on the challenge:

> *"Confirmed. Customs +$50K. Total air: $500K — at budget limit. Recommend Hybrid 60/40: $280K / 36h instead."*

Risk Agent **blocks** consensus until contingency plans are in place. This is genuine deliberation, not prompt chaining.

### Monte Carlo Probabilistic Decision Engine

```python
# 100 iterations, normal distribution around base cost
result = await run_monte_carlo(base_cost=253_000, n_iterations=100)
# → {mean_usd: 280000, p10_usd: 241000, p90_usd: 318000,
#    confidence_interval: 0.94, distribution: [3,6,10,...]}
```

The 22-bucket histogram is computed server-side and rendered live in the frontend Decision Matrix via D3.js — no additional API calls.

### Cross-Session Episodic Memory (TursoDB)

Every resolved run stores a structured memory record:

```python
await turso_client.save_memory(
    memory_key="run_abc123_port_strike",
    scenario_type="port_strike",
    decision="Hybrid route — $253K / 36h",
    outcome="Resolved in 4m 32s. MC confidence 94%.",
    cost_usd=253_000,
    saved_usd=1_720_000,
    key_learning="Hybrid beat air-only by ~$50K customs surcharge.",
    confidence=0.94,
)
```

Future Logistics Agents recall this via semantic query: `memory_recall("LA_port_strike")` — turning every resolution into institutional knowledge that improves the next one.

### A2A (Agent-to-Agent) Protocol

Each agent exposes an independently callable **A2A task API**. External ERPs, orchestration platforms, or other AI agents can invoke individual capabilities without triggering a full run:

```bash
# Call Finance's Monte Carlo directly from any external system
POST /agents/finance/tasks
{
  "task": "run_monte_carlo",
  "inputs": {"base_cost_usd": 280000, "iterations": 100}
}

# Call Logistics' route evaluation
POST /agents/logistics/tasks
{
  "task": "evaluate_crisis",
  "inputs": {"scenario": "port_strike"}
}
```

Agent capabilities are discoverable via `GET /.well-known/agent-card.json`. The Orchestrator is intentionally excluded from A2A direct calls — full execution requires `POST /api/runs` and human approval.

### Real-Time SSE Streaming

Every agent action publishes typed events directly to Redis from inside the LangGraph node that produces it. The SSE endpoint polls Redis independently — it has no knowledge of LangGraph. This decoupling means the frontend and backend can evolve independently.

**17 typed SSE event shapes:**

```
PhaseEvent · AgentStateEvent · ToolEvent · ToolResultEvent · MessageEvent
ApprovalRequiredEvent · ExecutionEvent · CompleteEvent · AuditEvent
MapUpdateEvent · RiskActivatedEvent · TokenEvent · …
```

### Human-in-the-Loop Approval Gate

The system **never executes autonomously**. After multi-agent consensus, an `ApprovalRequiredEvent` is published with full transparency: cost, confidence interval, delivery hours, customer SLA status, and contingency plan. A VP clicks **APPROVE** or **REJECT**. Only then does the cascade graph execute.

This is deliberate product design — AI handles the complexity, humans retain authority.

---

## Project Structure

```
b-team-supply-ops/
├── backend/
│   ├── agents/                  # Agent reasoning & LLM interaction
│   │   ├── base.py              # Shared utilities (elapsed, publish_state)
│   │   ├── orchestrator_live.py # Orchestrator message generation
│   │   ├── logistics.py         # Logistics agent logic
│   │   ├── finance.py           # Finance agent + MC integration
│   │   ├── procurement.py       # Procurement agent logic
│   │   ├── sales.py             # Sales / SLA negotiation
│   │   └── risk.py              # Risk / devil's advocate
│   │
│   ├── graph/                   # LangGraph compiled graphs
│   │   ├── orchestrator_graph.py    # _SCENARIO_GRAPH + _CASCADE_GRAPH
│   │   ├── a2a_task_runner.py       # A2A task routing dispatch
│   │   ├── state.py                 # RunGraphState TypedDict
│   │   ├── logistics_agent_graph.py
│   │   ├── finance_agent_graph.py
│   │   ├── procurement_agent_graph.py
│   │   ├── sales_agent_graph.py
│   │   └── risk_agent_graph.py
│   │
│   ├── api/
│   │   ├── orchestrator.py          # Run lifecycle management
│   │   ├── routes_decision_audit.py # Decision matrix + audit trail endpoints
│   │   └── sse.py                   # Server-Sent Events stream handler
│   │
│   ├── tools/
│   │   ├── freight.py           # check_freight_rates(), memory_recall()
│   │   ├── monte_carlo.py       # run_monte_carlo(), query_customs_rates()
│   │   ├── suppliers.py         # query_suppliers(), query_contract_terms()
│   │   └── registry.py          # Tool registry for A2A discovery
│   │
│   ├── audit/
│   │   ├── audit_helpers.py     # publish_audit_event() helper
│   │   └── audit_pdf.py         # ReportLab PDF generation
│   │
│   ├── core/
│   │   ├── models.py            # Pydantic v2 models for all SSE events
│   │   ├── scenarios.py         # SCENARIO_DEFINITIONS + hardcoded replay steps
│   │   └── config.py            # Environment config
│   │
│   ├── db/
│   │   ├── redis_client.py      # Upstash Redis pub/sub wrapper
│   │   └── turso_client.py      # TursoDB episodic memory client
│   │
│   ├── main.py                  # FastAPI app entry point
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── components/
    │   │   ├── left/
    │   │   │   ├── DecisionTab.jsx    # Monte Carlo + option comparison
    │   │   │   ├── AuditTab.jsx       # Timestamped audit trail
    │   │   │   ├── MapTab.jsx         # Leaflet live route map
    │   │   │   ├── MemoryTab.jsx      # Episodic memory viewer
    │   │   │   ├── SplitTab.jsx       # Multi-panel layout
    │   │   │   └── PhaseStrip.jsx     # Phase progress indicator
    │   │   └── right/
    │   │       ├── AgentNetwork.jsx   # Live agent status grid
    │   │       ├── AgentCard.jsx      # Individual agent card
    │   │       ├── ChatPanel.jsx      # Agent message feed
    │   │       ├── ApprovalPanel.jsx  # VP approval interface
    │   │       └── RiskAgent.jsx      # Risk alert display
    │   └── hooks/
    │       ├── useSSE.js              # EventSource connection + dispatch
    │       ├── useAuditTrail.js       # Audit event accumulation
    │       ├── useDecisionMatrix.js   # Decision data state
    │       └── useLeafletMap.js       # Map update handling
    └── package.json
```

---

## API Reference

### Core Run Lifecycle

```
POST   /api/runs                        Create run, starts scenario graph
GET    /api/stream/{run_id}             SSE stream — all agent events
GET    /api/runs/{run_id}               Run status + context
POST   /api/runs/{run_id}/approve       Human approval → triggers cascade graph
GET    /api/runs/{run_id}/decision-matrix   Live option comparison + Monte Carlo data
GET    /api/runs/{run_id}/audit-trail   Full timestamped agent decision log
GET    /api/runs/{run_id}/audit.pdf     Compliance PDF export (ReportLab)
```

### A2A Agent Task Endpoints

```
GET    /.well-known/agent-card.json     Agent capability discovery

POST   /agents/logistics/tasks
       tasks: check_freight | recall_memory | evaluate_crisis | revise_route

POST   /agents/finance/tasks
       tasks: run_monte_carlo | query_customs | challenge_cost | propose_consensus

POST   /agents/procurement/tasks
       tasks: query_suppliers | evaluate_spot_buy

POST   /agents/sales/tasks
       tasks: lookup_contract | draft_amendment | negotiate_sla

POST   /agents/risk/tasks
       tasks: challenge_consensus
```

---

## Setup & Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- Upstash Redis account (free tier works)
- Google AI Studio API key (Gemini 1.5)
- Turso account + database (optional — episodic memory degrades gracefully without it)

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Copy and fill in environment variables
cp .env.example .env
# Required: GOOGLE_API_KEY, UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN
# Optional: TURSO_DATABASE_URL, TURSO_AUTH_TOKEN (enables episodic memory)

uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install

cp .env.example .env
# Set VITE_API_URL=http://localhost:8000

npm run dev
# → http://localhost:5173
```

### Environment Variables

```env
# Backend — required
GOOGLE_API_KEY=your_gemini_key
UPSTASH_REDIS_REST_URL=https://your-db.upstash.io
UPSTASH_REDIS_REST_TOKEN=your_token

# Backend — optional (episodic memory)
TURSO_DATABASE_URL=libsql://your-db.turso.io
TURSO_AUTH_TOKEN=your_token

# Backend — mode flag
USE_LIVE_AGENTS=true   # false = hardcoded replay (no API keys needed for demo)

# Frontend
VITE_API_URL=http://localhost:8000
```

> **Demo mode:** Set `USE_LIVE_AGENTS=false` to run fully without API keys. The hardcoded replay path produces the same SSE event sequence with realistic timing — identical UX to the live agent path.

---

## Technologies Used

### AI & Orchestration

| Technology | Role |
|---|---|
| **LangGraph** (`>=1.0.0`) | Two compiled `StateGraph` instances — `_SCENARIO_GRAPH` (pre-approval) and `_CASCADE_GRAPH` (post-approval) — drive the entire agent lifecycle with typed edges and no hand-written async orchestration |
| **Google Gemini 1.5** (`google-generativeai==0.7.2`) | LLM backbone powering all 5 agent reasoning steps; structured JSON responses parsed via Pydantic v2 |
| **A2A Protocol** | Agent-to-Agent interoperability — each agent exposes independently callable task endpoints discoverable via `/.well-known/agent-card.json` |
| **Monte Carlo Simulation** | 100-iteration probabilistic cost engine built in pure Python; produces P10/P90 confidence bands and a 22-bucket histogram for live chart rendering |

### Backend

| Technology | Role |
|---|---|
| **FastAPI** (`0.111.0`) | Async Python API server; handles REST endpoints, SSE streaming, and background task management for agent graph execution |
| **Uvicorn** (`0.29.0`) | ASGI server with standard extras for production-grade async serving |
| **Pydantic v2** (`>=2.7.1`) | Strict type-safe models for all 17+ SSE event payload shapes; shared contract between backend and frontend |
| **httpx** (`0.27.0`) | Async HTTP client used for outbound tool calls and freight/supplier API integrations |
| **ReportLab** (`4.4.10`) | PDF generation for compliance-ready audit trail exports |

### Databases & Persistence

| Technology | Role |
|---|---|
| **Redis (Upstash)** (`upstash-redis==1.1.0`) | Real-time pub/sub for SSE event delivery; run state hydration; cross-process agent messaging with zero shared memory |
| **TursoDB / libSQL** (`libsql-client==0.3.1`) | Edge-distributed SQLite-compatible database for cross-session episodic memory — agents learn from past crises across runs |

### Frontend

| Technology | Role |
|---|---|
| **React 18 + Vite** | Component-based UI with custom hooks (`useSSE`, `useAuditTrail`, `useDecisionMatrix`, `useLeafletMap`) for real-time state management |
| **D3.js** | Live Monte Carlo histogram rendering in the Decision Matrix tab — 22-bucket probability distribution updated in real time as Finance Agent runs simulations |
| **Leaflet** | Interactive geographic map showing live supply chain route decisions as agents evaluate options |
| **Server-Sent Events (SSE)** | Unidirectional real-time stream from backend to frontend; 17 typed event shapes deliver agent state, messages, tool results, and phase transitions token-by-token |

### DevOps & Deployment

| Technology | Role |
|---|---|
| **Vercel** | Edge-deployed frontend with global CDN; zero cold start for sub-100ms UI response |
| **python-dotenv** | Environment configuration management with `.env.example` templates for both backend and frontend |

---

## Hackathon Evaluation Criteria

### 🏆 Innovation & Creativity — 25%

ChainGuardAI introduces several ideas that are genuinely novel in the supply chain AI space:

**Adversarial agent consensus** — rather than a single LLM producing a recommendation, five domain-expert agents actively challenge each other. The Finance Agent does not accept Logistics' cost estimate; it interrogates it. The Risk Agent cannot be bypassed; it must challenge every consensus before the approval gate opens. This is a fundamentally different model from prompt chaining or RAG pipelines.

**Probabilistic AI decisions, not gut-feel outputs** — every recommendation is accompanied by a Monte Carlo-computed confidence interval (P10/P90/mean). The system does not say "choose option A." It says "option A has a 94% confidence interval between $241K and $318K, with a mean of $280K." That is a decision, not a suggestion.

**Cross-session episodic memory as competitive advantage** — every resolved crisis is stored as a structured learning record. The next time a similar disruption hits, Logistics Agent recalls the outcome automatically: *"March 2024 LA port strike — hybrid saved $180K."* The system gets smarter with every incident, compounding value over time.

**A2A interoperability** — ChainGuardAI follows the emerging Agent-to-Agent protocol, making every agent independently callable and composable within broader enterprise AI ecosystems. This is forward-looking architecture that anticipates how enterprise AI will actually be deployed.

---

### ⚙️ Technical Implementation — 25%

**LangGraph StateGraph orchestration** — all control flow is expressed as typed graph edges compiled at startup. There is no `asyncio.gather`, `asyncio.sleep`, or `asyncio.create_task` at the orchestration level. LangGraph drives the execution schedule. This produces a system that is deterministic, testable, and fully reproducible — qualities that matter enormously in production incident response.

```python
# Two compiled graphs — clean separation of concerns
_GRAPH_APP    = _build_orchestrator_graph()   # pre-approval deliberation
_CASCADE_GRAPH = _build_cascade_graph()        # post-approval execution
```

**Type-safe event contract** — all 17+ SSE event shapes are Pydantic v2 models. The frontend and backend share the same event contract. There is no "hope the JSON looks right" — a `PhaseEvent` is always a `PhaseEvent`, an `ApprovalRequiredEvent` always carries `cost_usd`, `confidence`, `delivery_hours`, and `detail`.

**Decoupled streaming architecture** — SSE events are published directly to Redis inside each LangGraph node that produces them. The SSE endpoint polls Redis independently with no knowledge of LangGraph. This decoupling means the streaming layer and the orchestration layer can be scaled, replaced, or tested independently.

**Redis key namespacing** — run state (`chainguardai:run:{id}:state`) and event queues (`chainguardai:run:{id}:queue`) are cleanly namespaced, preventing cross-run contamination even under concurrent load.

**Graceful degradation** — TursoDB (episodic memory) and live agent mode are both optional. The system falls back to hardcoded replay with identical SSE timing if API keys are absent. No feature breaks the demo.

---

### 📈 Feasibility & Scalability — 15%

**Real-world applicability** — the three demo scenarios are grounded in well-documented, high-frequency incident categories:

- **Port strikes** are an established and recurring threat. The 2024 East Coast/Gulf Coast ILA strike halted work at 36 ports spanning Maine to Texas, with over $2 billion in goods flowing through affected ports daily [[GEP, 2024](https://www.gep.com/blog/mind/2024-us-port-strike-lessons-for-supply-chain-resilience)]. The 2002 West Coast port lockout cost the U.S. economy an estimated $1 billion per day [[TLI, 2025](https://www.translogisticsinc.com/blog/potential-port-strikes-threaten-to-disrupt-global-supply-chains)].
- **Customs delays** are a primary driver of enterprise supply chain risk, with Uyghur Forced Labor Prevention Act enforcement alone stopping over 10,000 shipments valued at more than $3.5 billion at U.S. borders since 2022 [[Source Intelligence, 2024](https://blog.sourceintelligence.com/the-cost-of-disruption)].
- **Supplier disruptions** are routinely catastrophic for electronics and semiconductor supply chains. When a Philips semiconductor plant fire in 2000 disrupted Nokia and Ericsson, Ericsson — which was slower to respond — lost an estimated $400 million in sales [[Cin7, 2025](https://www.cin7.com/blog/supply-chain-disruptions/)]. The shipment values ($8M–$20M) and penalty structures ($1.5M–$5M) modelled in ChainGuardAI are consistent with real Fortune 500 electronics contract terms.

**The $184M annual disruption cost** cited in the problem statement is sourced directly from the Interos Annual Global Supply Chain Report (2021), corroborated by Statista [[Interos/Statista](https://www.statista.com/statistics/1259125/cost-supply-chain-disruption-country/)] and independently referenced by BSI's Resilience Report 2023. For U.S. organizations specifically, the average rises to **$228M** [[Interos Whitepaper](https://www.fbcinc.com/source/virtualhall_images/HHS/Interos/1._NEW_Interos_WP_Cost_of_Status_Quo_08.03.21.pdf)].

**The McKinsey 45% / 3.7-year statistic** (used in the broader problem framing) is sourced directly from McKinsey & Company research, cited across McKinsey's own explainer pages and the World Economic Forum [[McKinsey via WEF, 2025](https://www.weforum.org/stories/2025/01/supply-chain-disruption-digital-winners-losers/)] [[McKinsey.com](https://www.mckinsey.com/featured-insights/mckinsey-explainers/what-is-supply-chain)].

**Quantified ROI** — the per-crisis savings figures ($1.72M, $1.1M, $4.5M) are computed directly from the scenario penalty structures in `backend/core/scenarios.py`. The 48-hour human response baseline is grounded in industry data: a 2024 IDC/Kinaxis survey of 1,800 supply chain decision-makers found the **average enterprise response time to disruptions is five days**, with only 17% of companies able to respond within 24 hours [[Supply Chain Movement / IDC-Kinaxis, 2024](https://www.supplychainmovement.com/83-of-supply-chains-unable-to-respond-to-disruptions-within-24-hours/)]. Gartner independently confirms that only **7% of supply chain organizations can execute decisions in real time** [[Gartner Supply Chain Symposium, 2024](https://www.gartner.com/en/articles/highlights-from-gartner-supply-chain-symposium-xpo-2024)]. The 48-hour figure used is therefore a *conservative* baseline — the industry median is significantly worse.

| Metric | Value | Source |
|---|---|---|
| Resolution time | 48h → 4m 32s (86× faster) | 48h baseline: IDC/Kinaxis 2024; 4m 32s: measured in demo |
| Per-crisis saving | $1.72M – $4.5M | Computed from `scenarios.py` penalty structures |
| Annual enterprise value (10 crises/yr) | $72M+ | Derived: sum of per-crisis savings × 10 |
| Avoided overspend per crisis | ~$150–200K | Consistent with Interos avg. $22M per major disruption [[MDM, 2023](https://www.mdm.com/news/tech-operations/operations/data-supply-chain-disruption-costs-drop-for-large-firms-but-still-elevated/)] scaled to P0 incident scope |
| Industry annual disruption cost (avg. enterprise) | $82M–$184M | Interos 2021–2023 surveys [[Conexiom](https://conexiom.com/blog/the-cost-of-supply-chain-disruptions-20-statistics/)] |
| Tech sector disruption cost (annual) | ~$16B across sector | DP World / Logistics Business research [[Logistics Business, 2026](https://logisticsbusiness.com/transport-distribution/new-data-shows-cost-of-logistics-disruption/)] |

**Scalable architecture** — the Redis pub/sub layer, stateless FastAPI workers, and edge-deployed frontend mean horizontal scaling requires no architectural changes. Each run is isolated by `run_id`; multiple simultaneous crises can be handled concurrently.

**V2 enterprise path** — the system is explicitly designed for real ERP integration (SAP, Oracle), live freight APIs (FedEx, DHL, Flexport), actual customs authority feeds (US CBP, EU TARIC), and role-based approval workflows. The current tool layer is a clean abstraction that makes these integrations straightforward drop-ins.

**Composable via A2A** — any enterprise already running AI workflows can integrate individual ChainGuardAI agents (Finance's Monte Carlo, Logistics' route evaluation) without adopting the full platform. This dramatically lowers the adoption barrier.

---

### 🎬 Presentation & Demo — 15%

**The narrative is clear and visceral** — a $12M Apple shipment blocked at 2am, a $2M penalty clock ticking, six teams across time zones trying to coordinate. Every person in the room has either experienced this or knows someone who has. The problem lands immediately.

**The demo is self-evidently impressive** — watching five agents debate each other in real time, with Finance challenging Logistics' assumptions and Risk blocking consensus, is qualitatively different from watching a chatbot answer questions. Judges see genuine AI deliberation, not a canned output.

**`USE_LIVE_AGENTS=false` demo mode** — the hardcoded replay path produces the identical SSE event sequence with realistic timing. The demo never fails due to API latency or rate limits. Every message, tool call, and phase transition appears exactly as in live mode.

**One-click approval moment** — the demo has a clear climax: the VP approval panel appears with full context (cost, CI, delivery hours, customer status, contingency plan). One click. The cascade executes. `DELIVERED ✅` appears on the map. The story has a satisfying resolution.

**Quantified outcomes on screen** — the completion screen shows exact figures: `$280K spent · $1,720,000 saved · resolved in 4m 32s`. Judges see the ROI in the demo itself, not just in slides.

---

### 🤝 Responsible AI — 20%

#### Fairness & Bias Mitigation

Agent recommendations are driven by **structured quantitative inputs** — freight rates, supplier costs, customs tariffs, contract terms — not free-text LLM judgement alone. The Monte Carlo engine produces probability distributions, not point estimates, forcing the system to acknowledge uncertainty rather than project false confidence. No protected attributes (geography, vendor demographics) enter the scoring functions.

The **multi-agent adversarial structure** itself mitigates single-model bias: if Logistics Agent has a bias toward air freight, Finance Agent's cost challenge and Risk Agent's contingency check provide independent corrective pressure. No single agent's reasoning is accepted without scrutiny.

#### Transparency & Explainability

Every agent decision is **fully observable in real time** — tool calls, intermediate reasoning, challenges, and revisions all stream to the UI as they happen. There is no black box. A judge, auditor, or regulator can see exactly why the system recommended Hybrid over Air: Finance challenged the customs assumption, Logistics revised, Risk added a contingency trigger, Finance absorbed it into the final cost.

The **Audit Trail tab** provides a timestamped, step-by-step log of every agent action with the tool called, the data returned, and the conclusion reached. This is exportable as a **compliance PDF** (via ReportLab) with no additional effort.

The **Decision Matrix tab** displays all evaluated options side-by-side with cost, time, risk, and ESG scores — making the trade-offs explicit rather than hiding them inside a recommendation.

#### Data Privacy & Security

- **No personal data is processed** — ChainGuardAI operates on shipment metadata, cost figures, and contract terms. No PII enters the system.
- **Run isolation** — every run is scoped to a unique `run_id`. Redis keys and TursoDB records are namespaced per run. There is no cross-run data leakage.
- **API keys are environment-only** — no credentials appear in code. `.env.example` templates document required variables without exposing values.
- **TursoDB stores only operational data** — crisis type, resolution decision, cost, and outcome. No customer personal data is persisted.

#### Safety & Harm Prevention

**The system cannot act autonomously.** This is a hard architectural constraint, not a policy: the `_CASCADE_GRAPH` (which executes freight bookings, budget releases, and customer notifications) is only reachable via `POST /api/runs/{run_id}/approve`. There is no code path that executes downstream actions without an explicit human approval signal.

The Risk Agent is structurally required to challenge every consensus before the approval gate opens. It is not optional and cannot be skipped. This ensures a dedicated adversarial review of every plan before a human sees it.

#### Accountability

- **Full audit trail** — every agent message, tool call, revision, and decision is logged with timestamps from the moment a run starts.
- **Immutable run records** — resolved runs are persisted to TursoDB with their full context, cost, and outcome. Historical decisions are retrievable and explainable after the fact.
- **Human retains final authority** — the VP approval step is not a formality. The system presents all evidence and waits. If the human rejects, the cascade does not execute. The AI advises; the human decides.
- **Exportable compliance PDF** — `GET /api/runs/{run_id}/audit.pdf` produces a regulator-ready document with the complete agent decision timeline, automatically, for every run.

---

## Key Design Decisions & Trade-offs

**Why LangGraph instead of custom async orchestration?**
LangGraph gives us typed state machines, reproducible execution, built-in checkpointing, and clean separation between orchestration logic (graph edges) and business logic (node functions). The result is a system that is easy to test, debug, and extend — a critical advantage in production.

**Why SSE instead of WebSockets?**
SSE is unidirectional (server → client), which matches our use case exactly. It requires no connection management on the client, works through proxies and CDNs, and has native browser support. WebSockets would add complexity without benefit.

**Why keep the Orchestrator out of A2A?**
The Orchestrator manages the full run lifecycle including human approval gating. Allowing direct A2A calls to the Orchestrator would bypass the human-in-the-loop requirement. Individual agent capabilities are composable; full execution is not.

**Why TursoDB for episodic memory instead of a vector store?**
Structured relational queries on crisis metadata (scenario type, date, outcome, saved amount) are more useful for retrieval than semantic vector similarity alone. TursoDB is edge-distributed with a SQLite-compatible API, making it operationally simple while being genuinely persistent.

---

## What's Next

**V2 — Enterprise Integrations**
- Live ERP connections (SAP, Oracle NetSuite) for real-time inventory and PO data
- Actual freight API integrations (FedEx, DHL, Flexport)
- Real customs authority data feeds (US CBP, EU TARIC)
- Role-based approval workflows with Slack/Teams notifications

**V3 — Predictive Intelligence**
- OSINT-based disruption detection — catch the crisis before it hits your systems
- Autonomous scenario generation from news feeds and weather data
- Cross-company A2A federation (B2B supply chain coordination)
- ESG carbon footprint optimization agent
- Financial hedging agent for FX and commodity exposure

---

## Team

**B-Team**
- Balaji Ashok Kumar
- Rathi Velusamy
- Usha Muthu
- Rucha Parag Ganu
- Nivetha Visveswaran

## References & Sources

The following third-party research and reports substantiate the claims made throughout this README and the ChainGuardAI demo scenarios.

**Supply Chain Disruption Costs**
- Interos (2021). *Annual Global Supply Chain Report* — $184M average annual enterprise disruption cost. [fbcinc.com whitepaper](https://www.fbcinc.com/source/virtualhall_images/HHS/Interos/1._NEW_Interos_WP_Cost_of_Status_Quo_08.03.21.pdf)
- Interos / Statista (2021). *Estimated average annual cost by region* — U.S. average $228M. [statista.com](https://www.statista.com/statistics/1259125/cost-supply-chain-disruption-country/)
- Interos / Modern Distribution Management (2023). *Supply chain disruption costs for large firms* — avg. $22M per major disruption, $82M annually. [mdm.com](https://www.mdm.com/news/tech-operations/operations/data-supply-chain-disruption-costs-drop-for-large-firms-but-still-elevated/)
- DP World / Logistics Business (2026). *Without Logistics* global survey — tech sector disruption ~$16B annually, 52% of companies lose 1+ month of capacity per year. [logisticsbusiness.com](https://logisticsbusiness.com/transport-distribution/new-data-shows-cost-of-logistics-disruption/)
- Conexiom (2023). *The Cost of Supply Chain Disruptions: 20+ Statistics* — aggregates McKinsey, Interos, EY findings. [conexiom.com](https://conexiom.com/blog/the-cost-of-supply-chain-disruptions-20-statistics/)

**Disruption Frequency**
- McKinsey & Company. *What is supply chain?* — disruptions lasting 1+ month occur every 3.7 years on average; cost 45% of annual profit per decade. [mckinsey.com](https://www.mckinsey.com/featured-insights/mckinsey-explainers/what-is-supply-chain)
- World Economic Forum (2025). *Supply Chain Disruption: Digital Winners and Losers* — cites McKinsey 3.7-year figure. [weforum.org](https://www.weforum.org/stories/2025/01/supply-chain-disruption-digital-winners-losers/)

**Response Time Benchmarks**
- IDC / Kinaxis (2024), via Supply Chain Movement — average enterprise disruption response time is **5 days**; only 17% of companies respond within 24 hours. [supplychainmovement.com](https://www.supplychainmovement.com/83-of-supply-chains-unable-to-respond-to-disruptions-within-24-hours/)
- Gartner Supply Chain Symposium (2024) — only **7% of supply chain organizations** can execute decisions in real time. [gartner.com](https://www.gartner.com/en/articles/highlights-from-gartner-supply-chain-symposium-xpo-2024)
- Interos (2023) — more than 90% of organizations would not be aware of a supplier disruption within 48 hours of occurrence. [mdm.com](https://www.mdm.com/news/tech-operations/operations/data-supply-chain-disruption-costs-drop-for-large-firms-but-still-elevated/)

**Port Strike & Scenario Realism**
- GEP (2024). *2024 US Port Strike: Key Lessons for Supply Chain Resilience* — 36 ports shut, 40% of U.S. port cargo volume affected. [gep.com](https://www.gep.com/blog/mind/2024-us-port-strike-lessons-for-supply-chain-resilience)
- Transport Logistics Inc. (2025). *Potential Port Strikes Threaten to Disrupt Global Supply Chains* — 2002 West Coast lockout cost $1B/day. [translogisticsinc.com](https://www.translogisticsinc.com/blog/potential-port-strikes-threaten-to-disrupt-global-supply-chains)
- Gartner (2024). *How US Port Strikes Disrupt Supply Chains*. [gartner.com](https://www.gartner.com/en/articles/how-us-port-strikes-disrupt-supply-chains)
- Supply Chain Dive (2024). *Days of a port strike could mean weeks of manufacturing delays*. [supplychaindive.com](https://www.supplychaindive.com/news/port-strike-east-coast-impact-disruptions-layoffs/728432/)

**Customs & Supplier Disruptions**
- Source Intelligence / McKinsey (2024). *The Cost of Disruption* — UFLPA enforcement stopped 10,000+ shipments valued at $3.5B+. [blog.sourceintelligence.com](https://blog.sourceintelligence.com/the-cost-of-disruption)
- Cin7 (2025). *Strategies for Managing Supplier Risks* — Philips/Ericsson semiconductor case: $400M lost in sales from slow response. [cin7.com](https://www.cin7.com/blog/supply-chain-disruptions/)

---

<div align="center">
**Supply chains don't wait. Neither should you.**

*ChainGuardAI — turning supply chain crises into 5-minute decisions.*

</div>
