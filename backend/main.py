"""
main.py
───────
FastAPI application — Phase 1: Foundation

Routes:
  GET  /health                              Health check (Redis ping)
  GET  /api/scenarios                       List available scenarios
  POST /api/runs                            Start a new scenario run
  GET  /api/runs/{run_id}                   Get run state
  GET  /api/runs/{run_id}/decision-matrix   Live decision matrix (options + MC stats)
  GET  /api/runs/{run_id}/audit-trail       Ordered audit trail for a run
  GET  /api/stream/{run_id}                 SSE stream (EventSource connects here)
  POST /api/runs/{run_id}/approve           Human approves the AI recommendation
  GET  /agents/{name}/.well-known/agent.json   A2A agent cards

Run locally:
  uvicorn main:app --reload --port 8000
"""

import asyncio
import uuid
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import db.redis_client as redis_client
import api.orchestrator as orchestrator
from core.config import get_settings
from core.models import (
    CreateRunRequest, ApproveRunRequest,
    RunResponse, RunStatus, HealthResponse,
    ScenarioType,
    A2ATaskRequest, A2ATaskResult,
)
from core.scenarios import SCENARIO_DEFINITIONS
from api.sse import stream_run
from api.routes_decision_audit import router as decision_audit_router

settings = get_settings()


# ── Logging setup ───────────────────────────────────────────────────────────────────
# Call once here so every logger in the entire app (resolveiq.*, uvicorn, etc.)
# emits to stdout with timestamps.  Safe to call multiple times (idempotent).

def _setup_logging() -> None:
    fmt = logging.Formatter(
        fmt="%(asctime)s  %(levelname)-8s  %(name)-28s  %(message)s",
        datefmt="%H:%M:%S",
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(fmt)
    handler.setLevel(logging.DEBUG)

    root = logging.getLogger()
    if not root.handlers:          # avoid duplicate lines on uvicorn --reload
        root.addHandler(handler)
    root.setLevel(logging.DEBUG)

    # Quiet down noisy third-party loggers
    for noisy in ("httpx", "httpcore", "uvicorn.access", "asyncio", "multipart", "aiohttp"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

_setup_logging()
log = logging.getLogger("resolveiq.main")


# ── AsyncIO exception handler ────────────────────────────────────────────

def _handle_exception(loop, context):
    """Suppress expected connection errors from WebSocket backends."""
    exception = context.get('exception')
    msg = context.get('message', '')
    
    # Suppress expected Turso/WebSocket handshake errors
    if exception and 'WSServerHandshakeError' in type(exception).__name__:
        log.debug("Suppressed expected WebSocket error: %s", exception)
        return
    
    # Log other exceptions normally
    log.error("Unhandled exception in asyncio event loop: %s", context)

asyncio.get_event_loop().set_exception_handler(_handle_exception)


# ── Lifespan (startup / shutdown) ────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("🚀 ResolveIQ backend starting...")
    from agents.base import active_model_chain
    import db.turso_client as turso_client
    chain    = active_model_chain()
    redis_ok = await redis_client.health_check()
    
    # Initialize Turso schema with a timeout to prevent hanging
    try:
        turso_ok = await asyncio.wait_for(turso_client.init_schema(), timeout=30.0)
    except asyncio.TimeoutError:
        log.error("TursoDB schema initialization timed out (30s)")
        turso_ok = False
    except Exception as e:
        log.error("TursoDB schema initialization failed: %s", e)
        turso_ok = False

    if redis_ok:
        log.info("✅ Redis connected")
    else:
        log.warning("⚠️  Redis unreachable — check .env UPSTASH_REDIS_* values")

    if turso_ok:
        log.info("✅ TursoDB connected — persistent memory active")
    else:
        log.warning("⚠️  TursoDB not configured — using in-memory fallbacks (demo mode)")

    key_set = bool(settings.gemini_api_key and settings.gemini_api_key != "your_gemini_api_key_here")
    log.info("🤖 Agent mode    : %s",
             "LIVE (Gemini)" if orchestrator.USE_LIVE_AGENTS else "HARDCODED (Phase 1 fallback)")
    log.info("🔑 Gemini key    : %s",
             "SET" if key_set else "NOT SET — agents will emit hardcoded text")
    log.info("📋 Model chain   : %s",
             " → ".join(chain) if chain else "(empty — check GEMINI_MODEL_CHAIN in .env)")
    log.info("⏱️  Timeout/model : %ds  |  Rate-limit retries: %d  |  Backoff: %.1fs",
             settings.gemini_model_timeout,
             settings.gemini_rate_limit_retries,
             settings.gemini_rate_limit_backoff)
    yield
    log.info("👋 ResolveIQ backend shutting down")


# ── App ──────────────────────────────────────────────────────────────────

app = FastAPI(
    title="ResolveIQ API",
    description="AI-powered supply chain crisis resolution",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin, "http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(decision_audit_router, prefix="/api")


# ── Helpers ──────────────────────────────────────────────────────────────

def _run_url(run_id: str, path: str) -> str:
    base = f"http://localhost:{settings.port}" if settings.env == "development" else ""
    return f"{base}/api/runs/{run_id}/{path}"


# ── Routes ───────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health():
    """
    Health check — shows Redis, Gemini, active model chain, and agent mode.

    model_chain: the ordered list of models that will be tried on each agent call.
    agent_mode: "live" (real Gemini) or "hardcoded" (Phase 1 fallback).
    """
    import db.turso_client as turso_client
    from agents.base import active_model_chain
    redis_ok  = await redis_client.health_check()
    turso_ok  = await turso_client.health_check()
    gemini_ok = bool(settings.gemini_api_key and settings.gemini_api_key != "your_gemini_api_key_here")
    chain     = active_model_chain()
    return {
        "status":       "ok" if redis_ok else "degraded",
        "redis":        redis_ok,
        "gemini":       gemini_ok,
        "agent_mode":   "live" if orchestrator.USE_LIVE_AGENTS else "hardcoded",
        "model_chain":  chain,
        "model_chain_length": len(chain),
        "turso":        turso_ok,
        "env":          settings.env,
    }


@app.get("/api/scenarios", tags=["Scenarios"])
async def list_scenarios():
    """
    Returns all 3 selectable scenarios.
    Frontend uses this to populate the scenario dropdown.
    """
    return {
        "scenarios": [s.model_dump() for s in SCENARIO_DEFINITIONS.values()]
    }


@app.post("/api/runs", response_model=RunResponse, tags=["Runs"])
async def create_run(body: CreateRunRequest, background_tasks: BackgroundTasks):
    """
    Start a new scenario run.

    1. Generates a unique run_id
    2. Creates in-memory run state
    3. Kicks off background task that publishes events to Redis on schedule
    4. Returns immediately with run_id + SSE stream URL

    Frontend:
      const { run_id, stream_url } = await POST("/api/runs", { scenario });
      const es = new EventSource(stream_url);
    """
    if body.scenario not in SCENARIO_DEFINITIONS:
        raise HTTPException(status_code=400, detail=f"Unknown scenario: {body.scenario}")

    run_id = str(uuid.uuid4())
    orchestrator.create_run(run_id, body.scenario)

    # Kick off the scenario runner as a background task
    # It will publish events to Redis; SSE endpoint drains them to the browser
    background_tasks.add_task(
        orchestrator.run_scenario, run_id, body.scenario
    )

    return RunResponse(
        run_id=run_id,
        scenario=body.scenario,
        status=RunStatus.RUNNING,
        stream_url=f"/api/stream/{run_id}",
        approve_url=f"/api/runs/{run_id}/approve",
    )


@app.get("/api/runs/{run_id}", tags=["Runs"])
async def get_run(run_id: str):
    """Get the current state of a run."""
    run = orchestrator.get_run(run_id)
    if not run:
        # Try Redis fallback (reconnect case)
        run = await redis_client.get_run_state(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@app.get("/api/runs/history", tags=["Runs"])
async def run_history(limit: int = 20):
    """
    Returns the N most recent completed runs from TursoDB.
    Falls back to the in-memory _runs dict when TursoDB is not configured.
    Useful for the judge panel showing "X crises resolved today".
    """
    import db.turso_client as turso_client
    if turso_client.is_configured():
        return {"runs": await turso_client.list_recent_runs(limit)}
    # In-memory fallback
    from api.orchestrator import _runs
    recent = sorted(_runs.values(), key=lambda r: r.get("run_id", ""), reverse=True)[:limit]
    return {"runs": [{"run_id": r["run_id"], "scenario": r.get("scenario",""),
                      "status": r.get("status",""), "mode": r.get("mode","")} for r in recent]}


@app.get("/api/stream/{run_id}", tags=["Streaming"])
async def stream(run_id: str, request: Request):
    """
    SSE stream endpoint.

    Browser connects here via EventSource. This endpoint polls Redis
    and forwards events as SSE messages in real-time.

    Example client:
      const es = new EventSource('/api/stream/abc-123');
      es.onmessage = (e) => handleEvent(JSON.parse(e.data));
      es.onerror   = ()  => console.warn('SSE reconnecting...');
    """
    # Verify run exists
    run = orchestrator.get_run(run_id)
    if not run:
        run = await redis_client.get_run_state(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return await stream_run(run_id, request)


@app.post("/api/runs/{run_id}/approve", tags=["Runs"])
async def approve_run(run_id: str, body: ApproveRunRequest, background_tasks: BackgroundTasks):
    """
    Human approval endpoint.

    Called when the judge clicks APPROVE & EXECUTE in the frontend.
    Triggers the execution cascade as a background task.
    """
    run = orchestrator.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run["status"] != RunStatus.AWAITING_APPROVAL:
        raise HTTPException(
            status_code=409,
            detail=f"Run is not awaiting approval (current status: {run['status']})"
        )

    if not body.approved:
        # Rejection — fire re-negotiation cascade as background task
        orchestrator.set_run_status(run_id, RunStatus.RUNNING)
        background_tasks.add_task(orchestrator.run_rejection_cascade, run_id, body.notes or "")
        return {"run_id": run_id, "status": "renegotiating",
                "message": "Agents re-engaged for alternative proposal"}

    orchestrator.set_run_status(run_id, RunStatus.APPROVED)
    background_tasks.add_task(orchestrator.run_execution_cascade, run_id)

    return {"run_id": run_id, "status": "approved", "message": "Execution cascade started"}


# ── A2A Agent Cards ───────────────────────────────────────────────────────
# Compliant with A2A Protocol Specification v0.3.0 (released 2025-07-31).
# Authoritative schema source: github.com/a2aproject/A2A
#
# ┌─ AgentCard top-level fields (§4.4.1) ──────────────────────────────────┐
# │ REQUIRED                                                                │
# │   name            string   Human-readable agent name                   │
# │   description     string   CommonMark-safe purpose summary              │
# │   url             string   Base URL for JSON-RPC task calls (§9)        │
# │   version         string   Agent implementation version (semver)        │
# │   protocolVersion string   A2A spec version: "0.3.0"  ← singular str   │
# │   skills          Skill[]  ≥1 skill (§4.4.5)                           │
# │   defaultInputModes  string[]  MIME types accepted (text/plain, etc.)   │
# │   defaultOutputModes string[]  MIME types produced                      │
# │                                                                         │
# │ OPTIONAL                                                                │
# │   provider        {organization, url}   Operator identity (§4.4.2)     │
# │   documentationUrl  string  Link to docs                                │
# │   iconUrl         string   PNG/SVG branding icon (added v0.2.2)         │
# │   capabilities    {streaming, pushNotifications,                        │
# │                    stateTransitionHistory}  Feature flags (§4.4.3)      │
# │   supportedInterfaces  Interface[]  Multi-transport declaration (§4.4.6)│
# │     each: {url, protocolBinding, protocolVersion}                       │
# │   supportsAuthenticatedExtendedCard  bool  (added v0.2.1)               │
# │   securitySchemes  map<string, SecurityScheme>  (§4.5)                  │
# │   security         [{scheme: scopes}]  Required auth bindings           │
# └─────────────────────────────────────────────────────────────────────────┘
#
# Well-known URI (§8.2):  GET /.well-known/agent-card.json   (v0.3.0)
#   NOTE: v0.3.0 renamed agent.json → agent-card.json.
#   We serve BOTH paths for backwards compatibility.
#
# Task endpoint: POST /agents/{name}/tasks  (JSON-RPC 2.0, §9.4)
_BASE_URL = "http://localhost:8000"   # overridden in production via settings
_A2A_VERSION = "0.3.0"               # current A2A spec release

_PROVIDER = {
    "organization": "ResolveIQ",
    "url": "https://github.com/resolveiq",
}

def _interfaces(agent_id: str) -> list:
    """Declare all three A2A transport bindings for a given agent endpoint."""
    base = f"{_BASE_URL}/agents/{agent_id}"
    return [
        # Primary — JSON-RPC 2.0 over HTTP (§9), preferred transport
        {"url": f"{base}/tasks",      "protocolBinding": "JSONRPC",   "protocolVersion": _A2A_VERSION},
        # Secondary — HTTP+JSON/REST (§11)
        {"url": f"{base}/tasks/rest", "protocolBinding": "HTTP+JSON", "protocolVersion": _A2A_VERSION},
    ]

AGENT_CARDS: dict[str, dict] = {

    # ── Orchestrator ──────────────────────────────────────────────────────
    "orchestrator": {
        # --- Identity ---
        "name": "ResolveIQ Orchestrator",
        "description": (
            "Master coordinator for P0 supply-chain crisis resolution. "
            "Broadcasts the crisis brief to all specialist agents, tracks "
            "round-by-round consensus, triggers the Risk devil's-advocate "
            "check, and gates on human approval before execution. "
            "Implemented as a LangGraph StateGraph over RunGraphState."
        ),
        "url": f"{_BASE_URL}/agents/orchestrator/tasks",
        "version": "1.0.0",
        "protocolVersion": _A2A_VERSION,            # ← singular string per v0.3.0 spec

        # --- Provider (§4.4.2) ---
        "provider": _PROVIDER,
        "documentationUrl": f"{_BASE_URL}/docs#/A2A",

        # --- Multi-transport declaration (§4.4.6) ---
        "supportedInterfaces": _interfaces("orchestrator"),
        "supportsAuthenticatedExtendedCard": False,  # no private skill surface yet

        # --- Capability flags (§4.4.3) ---
        "capabilities": {
            "streaming": True,              # SSE token-by-token via stream_gemini()
            "pushNotifications": False,
            "stateTransitionHistory": True, # run_context carries full round history
        },

        # --- Content negotiation ---
        # Agents exchange crisis payloads as JSON; humans read streamed text
        "defaultInputModes":  ["application/json", "text/plain"],
        "defaultOutputModes": ["application/json", "text/event-stream"],

        # --- No auth required (open demo endpoint) ---
        # Omitting securitySchemes/security signals public access per spec convention

        # --- Skills (§4.4.5) — each skill must have id, name, description, tags ---
        "skills": [
            {
                "id": "crisis-broadcast",
                "name": "Crisis Broadcast",
                "description": (
                    "Receives a P0 crisis payload (scenario + run_id) and fans "
                    "out the brief to Logistics, Procurement, Finance, Sales, and "
                    "Risk agents in the correct dependency order, starting the "
                    "resolution clock and publishing ACTIVATING state events."
                ),
                "tags": ["orchestration", "crisis", "broadcast", "multi-agent", "supply-chain"],
                "examples": [
                    "Start resolution for SC-2024-8891: Long Beach port strike, budget $500K, deadline 48h",
                    "Broadcast customs-delay scenario for AAPL shipment to all agents",
                ],
                "inputModes":  ["application/json"],
                "outputModes": ["application/json", "text/event-stream"],
            },
            {
                "id": "consensus-detection",
                "name": "Consensus Detection",
                "description": (
                    "Polls round_context after each agent completes. Detects when "
                    "Logistics, Finance, Procurement, and Sales have all set "
                    "consensus=True, then triggers the Risk agent's devil's-advocate "
                    "check before requesting human approval."
                ),
                "tags": ["consensus", "multi-agent", "coordination", "langgraph"],
                "examples": [
                    "Check if all agents agree on the hybrid-60-40 route",
                ],
                "inputModes":  ["application/json"],
                "outputModes": ["application/json"],
            },
            {
                "id": "approval-workflow",
                "name": "Human-in-the-Loop Approval",
                "description": (
                    "Emits an ApprovalRequiredEvent (option, cost_usd, reserve_usd, "
                    "delivery_hours, confidence) once consensus is reached. Persists "
                    "run state and episodic memory to TursoDB on approval, then "
                    "executes the confirmed plan."
                ),
                "tags": ["human-in-the-loop", "approval", "hitl", "execution", "turso"],
                "examples": [
                    "Submit hybrid route for human approval at $280K + $20K reserve",
                ],
                "inputModes":  ["application/json"],
                "outputModes": ["application/json"],
            },
        ],
    },

    # ── Logistics ─────────────────────────────────────────────────────────
    "logistics": {
        "name": "ResolveIQ Logistics Agent",
        "description": (
            "Evaluates freight routes under crisis conditions. Fetches live "
            "carrier rates (air / sea / hybrid) via check_freight_rates(), "
            "recalls matching historical incidents from TursoDB episodic memory, "
            "and revises its recommendation when Finance surfaces a hidden "
            "customs surcharge. Powered by Gemini via LangGraph subgraph."
        ),
        "url": f"{_BASE_URL}/agents/logistics/tasks",
        "version": "1.0.0",
        "protocolVersion": _A2A_VERSION,
        "provider": _PROVIDER,
        "documentationUrl": f"{_BASE_URL}/docs#/A2A",
        "supportedInterfaces": _interfaces("logistics"),
        "supportsAuthenticatedExtendedCard": False,
        "capabilities": {
            "streaming": True,
            "pushNotifications": False,
            "stateTransitionHistory": False,
        },
        "defaultInputModes":  ["application/json", "text/plain"],
        "defaultOutputModes": ["application/json", "text/event-stream"],
        "skills": [
            {
                "id": "freight-rate-evaluation",
                "name": "Freight Rate Evaluation",
                "description": (
                    "Calls check_freight_rates(scenario) to fetch carrier, route, "
                    "cost_usd, transit_hours, risk_level, and capacity_pct for all "
                    "available options, then recommends the optimal route with "
                    "explicit cost / time / risk tradeoffs."
                ),
                "tags": ["freight", "routing", "logistics", "supply-chain", "cost", "carrier"],
                "examples": [
                    "Evaluate freight options for Long Beach port-strike: air-LAX vs hybrid-60-40",
                    "Compare FedEx air ($450K/24h) vs hybrid ONE+FedEx ($253K/36h)",
                ],
                "inputModes":  ["application/json"],
                "outputModes": ["application/json", "text/event-stream"],
            },
            {
                "id": "episodic-memory-recall",
                "name": "Episodic Memory Recall",
                "description": (
                    "Queries TursoDB (falling back to in-memory bank) for the "
                    "closest historical crisis match by keyword + scenario type. "
                    "Returns: date, decision taken, outcome, cost_usd, saved_usd, "
                    "key_learning, confidence — grounding the recommendation in "
                    "verified precedent."
                ),
                "tags": ["memory", "episodic", "precedent", "historical", "turso", "rag"],
                "examples": [
                    "Recall the March 2024 ILWU Long Beach strike — what did we choose?",
                    "Find a precedent matching customs-delay + semiconductor + Shenzhen",
                ],
                "inputModes":  ["application/json", "text/plain"],
                "outputModes": ["application/json"],
            },
            {
                "id": "route-recalculation",
                "name": "Route Recalculation",
                "description": (
                    "Calls recalculate_route() after a Finance cost challenge. "
                    "Applies the customs surcharge to the air-only baseline, "
                    "confirms the revised total breaches the budget cap, and "
                    "formally re-endorses the hybrid as the dominant option."
                ),
                "tags": ["recalculation", "revision", "cost-challenge", "hybrid", "surcharge"],
                "examples": [
                    "Recalculate air-LAX after +$50K ILWU expedited-customs surcharge",
                    "Show revised air total vs hybrid when customs adds $22K strike fee",
                ],
                "inputModes":  ["application/json"],
                "outputModes": ["application/json", "text/event-stream"],
            },
        ],
    },

    # ── Finance ───────────────────────────────────────────────────────────
    "finance": {
        "name": "ResolveIQ Finance Agent",
        "description": (
            "Quantitative challenger and final cost authoriser. Runs 100-iteration "
            "Monte Carlo simulations (Box-Muller, σ=15%) over the proposed route "
            "cost, cross-checks scenario-specific customs rates to surface hidden "
            "surcharges, issues a precise cost challenge to Logistics, then — after "
            "Risk weighs in — broadcasts the authorised total with confidence interval."
        ),
        "url": f"{_BASE_URL}/agents/finance/tasks",
        "version": "1.0.0",
        "protocolVersion": _A2A_VERSION,
        "provider": _PROVIDER,
        "documentationUrl": f"{_BASE_URL}/docs#/A2A",
        "supportedInterfaces": _interfaces("finance"),
        "supportsAuthenticatedExtendedCard": False,
        "capabilities": {
            "streaming": True,
            "pushNotifications": False,
            "stateTransitionHistory": False,
        },
        "defaultInputModes":  ["application/json", "text/plain"],
        "defaultOutputModes": ["application/json", "text/event-stream"],
        "skills": [
            {
                "id": "monte-carlo-simulation",
                "name": "Monte Carlo Cost Simulation",
                "description": (
                    "Runs N iterations (default 100) of a Box-Muller normal "
                    "distribution centred on the proposed route cost (σ=15%). "
                    "Returns mean_usd, p10_usd, p90_usd, std_usd, "
                    "confidence_interval, and a 22-bucket histogram for the "
                    "frontend D3 chart."
                ),
                "tags": ["monte-carlo", "simulation", "statistics", "cost", "p10", "p90", "confidence"],
                "examples": [
                    "Run 100 Monte Carlo iterations on hybrid route at $253K",
                    "What is the P10/P90 cost band for the supplier-breach air option?",
                ],
                "inputModes":  ["application/json"],
                "outputModes": ["application/json"],
            },
            {
                "id": "customs-rate-query",
                "name": "Customs Rate Query",
                "description": (
                    "Retrieves scenario-specific customs clearance costs: standard, "
                    "expedited, active-strike surcharge tiers, and processing hours. "
                    "Used to challenge Logistics estimates that omit LAX Tier-3 "
                    "expedited-strike fees ($50K all-in for port-strike scenario)."
                ),
                "tags": ["customs", "tariff", "surcharge", "LAX", "ILWU", "clearance"],
                "examples": [
                    "What is the all-in expedited customs cost at LAX during an ILWU strike?",
                    "Query Tier-3 surcharge for port-strike scenario — standard vs expedited",
                ],
                "inputModes":  ["application/json"],
                "outputModes": ["application/json"],
            },
            {
                "id": "consensus-proposal",
                "name": "Consensus Proposal & Final Authorisation",
                "description": (
                    "After Risk flags a specific failure mode, Finance absorbs a "
                    "$20K contingency reserve and broadcasts the final authorised "
                    "total (hybrid_cost + reserve) alongside the Monte Carlo "
                    "confidence interval to all agents, formally calling for "
                    "human approval."
                ),
                "tags": ["consensus", "authorisation", "reserve", "approval", "final"],
                "examples": [
                    "Authorise $253K + $20K reserve = $273K at 94% CI — call for approval",
                    "Propose final consensus absorbing Risk's LAX ramp-worker contingency",
                ],
                "inputModes":  ["application/json"],
                "outputModes": ["application/json", "text/event-stream"],
            },
        ],
    },

    # ── Procurement ───────────────────────────────────────────────────────
    "procurement": {
        "name": "ResolveIQ Procurement Agent",
        "description": (
            "Spot-buy specialist. Queries the supplier catalog (TursoDB or "
            "in-memory fallback) for alternative sources near the crisis location. "
            "Reports per-supplier: name, location, stock_quantity_pct, "
            "total_cost_usd, transit_hours, cert_hours, risk_level, and notes. "
            "Flags quantity shortfalls that require hybrid logistics to bridge."
        ),
        "url": f"{_BASE_URL}/agents/procurement/tasks",
        "version": "1.0.0",
        "protocolVersion": _A2A_VERSION,
        "provider": _PROVIDER,
        "documentationUrl": f"{_BASE_URL}/docs#/A2A",
        "supportedInterfaces": _interfaces("procurement"),
        "supportsAuthenticatedExtendedCard": False,
        "capabilities": {
            "streaming": True,
            "pushNotifications": False,
            "stateTransitionHistory": False,
        },
        "defaultInputModes":  ["application/json", "text/plain"],
        "defaultOutputModes": ["application/json", "text/event-stream"],
        "skills": [
            {
                "id": "supplier-query",
                "name": "Supplier Query",
                "description": (
                    "Calls query_suppliers(scenario, location_hint) against TursoDB "
                    "or the in-memory catalog. Returns a list of viable spot-buy "
                    "sources with full logistics metadata so Logistics and Finance "
                    "can factor them into route + cost decisions."
                ),
                "tags": ["supplier", "spot-buy", "inventory", "procurement", "semiconductor", "catalog"],
                "examples": [
                    "Find spot-buy suppliers near Dallas for port-strike scenario, location_hint=dallas",
                    "Query alt-source suppliers for NVIDIA A100 equivalent during supplier-breach",
                ],
                "inputModes":  ["application/json"],
                "outputModes": ["application/json"],
            },
            {
                "id": "spot-buy-evaluation",
                "name": "Spot Buy Evaluation",
                "description": (
                    "Selects the primary supplier by cost and availability, computes "
                    "the blended cert+transit window, and explicitly flags if "
                    "stock_quantity_pct < 100% — signalling to the Orchestrator "
                    "that a hybrid logistics fill is required."
                ),
                "tags": ["spot-buy", "evaluation", "quantity", "certification", "shortfall"],
                "examples": [
                    "Texas Semiconductor: 80% qty, $380K, 12h transit, 4h cert — flag shortfall",
                    "Evaluate Dallas spot-buy viability for full 100% coverage of order",
                ],
                "inputModes":  ["application/json"],
                "outputModes": ["application/json", "text/event-stream"],
            },
        ],
    },

    # ── Sales ─────────────────────────────────────────────────────────────
    "sales": {
        "name": "ResolveIQ Sales Agent",
        "description": (
            "Customer relationship guardian. Retrieves live contract terms "
            "(SLA deadline, penalty clauses, extension eligibility, Q3 "
            "priority-allocation benefits) via query_contract_terms(). "
            "Drafts and confirms SLA amendments in real time via "
            "draft_sla_amendment(), securing written extensions before "
            "the penalty clock expires."
        ),
        "url": f"{_BASE_URL}/agents/sales/tasks",
        "version": "1.0.0",
        "protocolVersion": _A2A_VERSION,
        "provider": _PROVIDER,
        "documentationUrl": f"{_BASE_URL}/docs#/A2A",
        "supportedInterfaces": _interfaces("sales"),
        "supportsAuthenticatedExtendedCard": False,
        "capabilities": {
            "streaming": True,
            "pushNotifications": False,
            "stateTransitionHistory": False,
        },
        "defaultInputModes":  ["application/json", "text/plain"],
        "defaultOutputModes": ["application/json", "text/event-stream"],
        "skills": [
            {
                "id": "contract-terms-lookup",
                "name": "Contract Terms Lookup",
                "description": (
                    "Calls query_contract_terms(scenario) to retrieve the active "
                    "SLA: customer, contract_ref, sla_hours, penalty_usd, "
                    "extension_hours, extension_accepted, penalty_waived, "
                    "q3_priority_benefit, and amendment_ref."
                ),
                "tags": ["contract", "SLA", "terms", "penalty", "customer", "extension"],
                "examples": [
                    "Look up AAPL-SC-2024-Q3 contract terms for Apple port-strike scenario",
                    "What are the SLA penalty and extension clauses for the NVIDIA breach case?",
                ],
                "inputModes":  ["application/json", "text/plain"],
                "outputModes": ["application/json"],
            },
            {
                "id": "sla-amendment-drafting",
                "name": "SLA Amendment Drafting",
                "description": (
                    "Calls draft_sla_amendment(scenario, extension_hours, "
                    "new_delivery_plan) to generate a confirmed amendment record: "
                    "amendment_id, extension_granted, new delivery plan text, "
                    "penalty_waived status, and next_legal_step. "
                    "Result is published as a rich card in the crisis chat."
                ),
                "tags": ["SLA", "amendment", "negotiation", "extension", "penalty-waiver", "legal"],
                "examples": [
                    "Draft 36h extension for Apple: hybrid route 36h ETA at $253K",
                    "Confirm Samsung force-majeure amendment SMSG-FM-2024-0891",
                ],
                "inputModes":  ["application/json"],
                "outputModes": ["application/json", "text/event-stream"],
            },
        ],
    },

    # ── Risk ──────────────────────────────────────────────────────────────
    "risk": {
        "name": "ResolveIQ Risk Agent — Devil's Advocate",
        "description": (
            "Activates ONLY after all four specialist agents have reached consensus. "
            "Reads the full agreed plan and the scenario-specific risk intelligence "
            "brief, then identifies the single most dangerous operational failure "
            "mode — naming a specific company, person, system, or location. "
            "States severity and prescribes one concrete mitigation or backup "
            "trigger. Never agrees with consensus; challenging it is its sole role."
        ),
        "url": f"{_BASE_URL}/agents/risk/tasks",
        "version": "1.0.0",
        "protocolVersion": _A2A_VERSION,
        "provider": _PROVIDER,
        "documentationUrl": f"{_BASE_URL}/docs#/A2A",
        "supportedInterfaces": _interfaces("risk"),
        "supportsAuthenticatedExtendedCard": False,
        "capabilities": {
            "streaming": True,
            "pushNotifications": False,
            "stateTransitionHistory": False,
        },
        "defaultInputModes":  ["application/json"],
        "defaultOutputModes": ["application/json", "text/event-stream"],
        "skills": [
            {
                "id": "consensus-challenge",
                "name": "Consensus Challenge (Devil's Advocate)",
                "description": (
                    "Ingests the full run_context (logistics, finance, sales, "
                    "procurement outputs) plus injected scenario-specific risk "
                    "intelligence (e.g. LAX ramp-worker ILWU solidarity risk, "
                    "Busan ATA carnet single-point failure, NVIDIA Friday cert "
                    "cutoff window) and produces a structured challenge: "
                    "⚠ Consensus challenge: [specific risk]. [Severity if it "
                    "fails]. Recommend [backup trigger / mitigation]."
                ),
                "tags": [
                    "risk", "devils-advocate", "failure-mode", "single-point-of-failure",
                    "contingency", "post-consensus", "supply-chain",
                ],
                "examples": [
                    "Challenge hybrid-60-40 LAX plan: are ILWU ramp workers covered?",
                    "Identify Busan carnet single-point failure in customs-delay plan",
                    "Flag NVIDIA Friday 4pm cert cutoff risk for supplier-breach plan",
                ],
                "inputModes":  ["application/json"],
                "outputModes": ["application/json", "text/event-stream"],
            },
        ],
    },
}


@app.get("/agents/{agent_name}/.well-known/agent-card.json", tags=["A2A"])
async def agent_card(agent_name: str):
    """
    A2A Protocol agent discovery endpoint — v0.3.0 well-known URI (§8.2).

    URI changed from agent.json → agent-card.json in v0.3.0 (2025-07-31).
    Returns the full AgentCard JSON for the named agent, compliant with
    A2A v0.3.0: protocolVersion (singular string), supportedInterfaces,
    supportsAuthenticatedExtendedCard, provider, capabilities, typed skills.

    See also: GET /agents/{name}/.well-known/agent.json  (backwards compat alias)
    Task endpoint: POST /agents/{name}/tasks  (JSON-RPC 2.0, §9.4)
    """
    if agent_name not in AGENT_CARDS:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    return JSONResponse(
        content=AGENT_CARDS[agent_name],
        media_type="application/json",
        headers={"X-A2A-Protocol-Version": _A2A_VERSION},
    )


@app.get("/agents/{agent_name}/.well-known/agent.json", tags=["A2A"])
async def agent_card_legacy(agent_name: str):
    """
    Backwards-compatibility alias for pre-v0.3.0 A2A clients.

    The canonical URI is now /.well-known/agent-card.json (v0.3.0).
    This endpoint returns the identical payload so older clients and
    any hardcoded links in docs/demos continue to work.
    """
    return await agent_card(agent_name)


@app.get("/agents", tags=["A2A"])
async def list_agents():
    """
    Registry of all ResolveIQ A2A agents.

    Returns each agent's agentId, canonical card URL (v0.3.0 URI),
    task endpoint, version, protocolVersion, skill index (id + name + tags),
    and capability flags — enough for an A2A client to select and invoke
    the right agent without fetching every individual card.
    """
    return {
        "protocolVersion": _A2A_VERSION,
        "totalAgents": len(AGENT_CARDS),
        "agents": [
            {
                "agentId":       agent_id,
                "name":          card["name"],
                # v0.3.0 canonical URI
                "cardUrl":       f"/agents/{agent_id}/.well-known/agent-card.json",
                # legacy URI for older clients
                "cardUrlLegacy": f"/agents/{agent_id}/.well-known/agent.json",
                "taskUrl":       card["url"],
                "version":       card["version"],
                "protocolVersion": card["protocolVersion"],
                "description":   card["description"],
                "capabilities":  card["capabilities"],
                "supportedInterfaces": card.get("supportedInterfaces", []),
                # Slim skill index — full skill detail lives in the card
                "skills": [
                    {"id": s["id"], "name": s["name"], "tags": s["tags"]}
                    for s in card.get("skills", [])
                ],
            }
            for agent_id, card in AGENT_CARDS.items()
        ],
    }


# ── A2A Task Execution ────────────────────────────────────────────────────

@app.post(
    "/agents/{agent_name}/tasks",
    response_model=A2ATaskResult,
    tags=["A2A"],
    summary="Execute an A2A task on a specialist agent",
    response_description="A2A TaskResult with structured outputs and agent messages",
)
async def execute_agent_task(agent_name: str, body: A2ATaskRequest):
    """
    POST /agents/{agent_name}/tasks  — A2A task execution endpoint (§9.4 / §11.3).

    Routes the task request to the named agent's LangGraph subgraph and
    returns a structured A2ATaskResult.  The existing /api/runs* and SSE
    endpoints are unaffected.

    **Agent names**: logistics, finance, procurement, sales, risk.
    The orchestrator is excluded from direct task calls (use POST /api/runs).

    **Supported tasks per agent**:

    | Agent        | Tasks                                                           |
    |--------------|-----------------------------------------------------------------|
    | logistics    | check_freight, recall_memory, evaluate_crisis, revise_route     |
    | finance      | run_monte_carlo, query_customs, challenge_cost, propose_consensus |
    | procurement  | query_suppliers, evaluate_spot_buy                              |
    | sales        | lookup_contract, draft_amendment, negotiate_sla                 |
    | risk         | challenge_consensus                                             |

    **Streaming**: SSE token events are published to Redis under `task_id`.
    Open `GET /api/stream/{task_id}` *before* calling this endpoint to receive
    Gemini tokens as they stream.

    **Common `inputs` keys**:
    - `scenario`: `"port_strike"` | `"customs_delay"` | `"supplier_breach"`
    - `logistics`: upstream logistics output dict (for finance / sales / risk)
    - `hybrid_cost_usd`: overrides default $253K for downstream agents
    - `base_cost_usd`: Monte Carlo base cost (finance `run_monte_carlo`)
    - `challenge`: Finance challenge text (logistics `revise_route`)
    - `reserve_usd`: contingency reserve (finance `propose_consensus`)
    - `query`: free-text search (logistics `recall_memory`)
    - `location_hint`: location string (procurement `query_suppliers`)
    """
    import uuid
    import time as _time
    from graph.a2a_task_runner import dispatch, SUPPORTED_TASKS

    # ── Validate agent ────────────────────────────────────────────────────
    if agent_name not in AGENT_CARDS:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Agent '{agent_name}' not found. "
                f"Available: {list(AGENT_CARDS)}"
            ),
        )
    if agent_name == "orchestrator":
        raise HTTPException(
            status_code=400,
            detail=(
                "The orchestrator is not directly addressable via A2A tasks. "
                "Use POST /api/runs to start a full scenario run."
            ),
        )

    # Allow caller to pin a task_id for addressable SSE streaming
    caller_meta = body.metadata or {}
    task_id     = caller_meta.get("task_id") or str(uuid.uuid4())
    started_at  = _time.time()

    try:
        result = await dispatch(
            agent_name=agent_name,
            task=body.task,
            inputs=body.inputs,
            task_id=task_id,
        )
    except Exception as exc:
        log.exception("A2A task failed: agent=%s task=%s", agent_name, body.task)
        return A2ATaskResult(
            status="failed",
            task_id=task_id,
            agent=agent_name,
            task=body.task,
            outputs={},
            messages=[],
            error=str(exc),
            metadata={
                "conversation_id": body.conversation_id,
                "duration_ms":     int((_time.time() - started_at) * 1000),
                **caller_meta,
            },
        )

    # Merge caller metadata with our routing/timing fields
    result_metadata: dict = {
        "conversation_id": body.conversation_id,
        "task_id":         task_id,
        "agent":           agent_name,
        "supported_tasks": SUPPORTED_TASKS.get(agent_name, []),
        "duration_ms":     int((_time.time() - started_at) * 1000),
        "stream_url":      f"/api/stream/{task_id}",
        # Agent-specific metadata surfaced by the runner
        **result.pop("metadata", {}),
        # Caller metadata last — lets callers override our fields if needed
        **caller_meta,
    }

    return A2ATaskResult(
        status="completed",
        task_id=task_id,
        agent=agent_name,
        task=result.get("task", body.task),
        outputs=result.get("outputs", {}),
        messages=[m for m in result.get("messages", []) if m],
        metadata=result_metadata,
    )
