"""
main.py
───────
FastAPI application — Phase 1: Foundation

Routes:
  GET  /health                        Health check (Redis ping)
  GET  /api/scenarios                 List available scenarios
  POST /api/runs                      Start a new scenario run
  GET  /api/runs/{run_id}             Get run state
  GET  /api/stream/{run_id}           SSE stream (EventSource connects here)
  POST /api/runs/{run_id}/approve     Human approves the AI recommendation
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

import redis_client
import orchestrator
from config import get_settings
from models import (
    CreateRunRequest, ApproveRunRequest,
    RunResponse, RunStatus, HealthResponse,
    ScenarioType,
)
from scenarios import SCENARIO_DEFINITIONS
from sse import stream_run

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
    for noisy in ("httpx", "httpcore", "uvicorn.access", "asyncio", "multipart"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

_setup_logging()
log = logging.getLogger("resolveiq.main")


# ── Lifespan (startup / shutdown) ────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("🚀 ResolveIQ backend starting...")
    from agents.base import active_model_chain
    import turso_client
    chain    = active_model_chain()
    redis_ok = await redis_client.health_check()
    turso_ok = await turso_client.init_schema()   # creates tables + seeds data

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
    import turso_client
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
    import turso_client
    if turso_client.is_configured():
        return {"runs": await turso_client.list_recent_runs(limit)}
    # In-memory fallback
    from orchestrator import _runs
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
        # Rejection — just update status (Phase 1 doesn't handle rejection flow)
        orchestrator.set_run_status(run_id, RunStatus.FAILED)
        return {"run_id": run_id, "status": "rejected"}

    orchestrator.set_run_status(run_id, RunStatus.APPROVED)
    background_tasks.add_task(orchestrator.run_execution_cascade, run_id)

    return {"run_id": run_id, "status": "approved", "message": "Execution cascade started"}


# ── A2A Agent Cards ───────────────────────────────────────────────────────
# These follow the A2A protocol spec. Judges can hit these URLs to see
# that each agent is a real independently-addressable service.

AGENT_CARDS = {
    "orchestrator": {
        "name": "Orchestrator Agent",
        "version": "1.0.0",
        "description": "Coordinates crisis resolution. Routes tasks to specialist agents, detects consensus, triggers human approval.",
        "capabilities": ["crisis_broadcast", "consensus_detection", "agent_routing", "approval_workflow"],
        "endpoint": "/agents/orchestrator/tasks",
        "protocol": "A2A/1.0",
    },
    "logistics": {
        "name": "Logistics Agent",
        "version": "1.0.0",
        "description": "Evaluates freight routes. Recalls historical precedents from episodic memory.",
        "capabilities": ["freight_routing", "memory_recall", "route_optimisation"],
        "tools": ["check_freight_rates", "memory_recall", "recalculate_route"],
        "endpoint": "/agents/logistics/tasks",
        "protocol": "A2A/1.0",
    },
    "finance": {
        "name": "Finance Agent",
        "version": "1.0.0",
        "description": "Runs Monte Carlo simulations. Challenges cost assumptions. Proposes consensus.",
        "capabilities": ["monte_carlo_simulation", "cost_challenge", "consensus_proposal"],
        "tools": ["run_monte_carlo", "query_customs_rates", "propose_consensus"],
        "endpoint": "/agents/finance/tasks",
        "protocol": "A2A/1.0",
    },
    "procurement": {
        "name": "Procurement Agent",
        "version": "1.0.0",
        "description": "Queries supplier catalog. Evaluates spot buy options and quantity constraints.",
        "capabilities": ["supplier_query", "spot_buy_evaluation", "certification_check"],
        "tools": ["query_suppliers", "check_inventory", "get_certification_time"],
        "endpoint": "/agents/procurement/tasks",
        "protocol": "A2A/1.0",
    },
    "sales": {
        "name": "Sales Agent",
        "version": "1.0.0",
        "description": "Reviews contract terms. Negotiates SLA amendments with customers.",
        "capabilities": ["contract_review", "sla_negotiation", "customer_notification"],
        "tools": ["query_contract_terms", "draft_sla_amendment", "notify_customer"],
        "endpoint": "/agents/sales/tasks",
        "protocol": "A2A/1.0",
    },
    "risk": {
        "name": "Risk Agent — Devil's Advocate",
        "version": "1.0.0",
        "description": "Activates AFTER consensus. Finds single points of failure. Forces contingency planning.",
        "capabilities": ["failure_analysis", "consensus_challenge", "contingency_trigger"],
        "tools": [],
        "activation": "post_consensus_only",
        "endpoint": "/agents/risk/tasks",
        "protocol": "A2A/1.0",
    },
}


@app.get("/agents/{agent_name}/.well-known/agent.json", tags=["A2A"])
async def agent_card(agent_name: str):
    """
    A2A protocol agent discovery endpoint.
    Returns the capability card for each agent.
    Judges can visit these URLs to verify the A2A architecture.
    """
    if agent_name not in AGENT_CARDS:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    return AGENT_CARDS[agent_name]


@app.get("/agents", tags=["A2A"])
async def list_agents():
    """List all registered agents and their card URLs."""
    return {
        "agents": [
            {
                "name": name,
                "card_url": f"/agents/{name}/.well-known/agent.json",
                **{k: v for k, v in card.items() if k in ("description", "capabilities", "version")},
            }
            for name, card in AGENT_CARDS.items()
        ]
    }
