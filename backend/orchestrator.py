"""
orchestrator.py
───────────────
Phase 2: Routes to either the live Gemini runner or the hardcoded fallback.

USE_LIVE_AGENTS = True   → calls real Gemini for all 5 agents
USE_LIVE_AGENTS = False  → hardcoded Phase 1 timing (safe fallback for demo)

The live runner lives in agents/orchestrator_live.py.
Both runners use the same Redis queue → same SSE endpoint → same frontend.
The frontend cannot tell the difference.
"""

import asyncio
import redis_client
from config import get_settings
from models import ScenarioType, RunStatus
from scenarios import get_hardcoded_steps, get_execution_steps

settings = get_settings()

# ── Feature flag ─────────────────────────────────────────────────────────
# Set USE_LIVE_AGENTS=true in .env to enable real Gemini agents.
# Falls back automatically to hardcoded if GEMINI_API_KEY is missing.
USE_LIVE_AGENTS: bool = (
    bool(settings.gemini_api_key)
    and settings.gemini_api_key != "your_gemini_api_key_here"
)

# ── In-memory run registry ───────────────────────────────────────────────
# Phase 3 moves this to TursoDB.
_runs: dict[str, dict] = {}


def get_run(run_id: str) -> dict | None:
    return _runs.get(run_id)


def create_run(run_id: str, scenario: ScenarioType) -> dict:
    run = {
        "run_id":   run_id,
        "scenario": scenario,
        "status":   RunStatus.PENDING,
        "approved": False,
        "mode":     "live" if USE_LIVE_AGENTS else "hardcoded",
    }
    _runs[run_id] = run
    return run


def set_run_status(run_id: str, status: RunStatus) -> None:
    if run_id in _runs:
        _runs[run_id]["status"] = status


# ── Scenario entry point ─────────────────────────────────────────────────

async def run_scenario(run_id: str, scenario: ScenarioType) -> None:
    """
    Chooses live vs hardcoded based on USE_LIVE_AGENTS flag.
    Always the function called by background_tasks.add_task().
    """
    set_run_status(run_id, RunStatus.RUNNING)

    if USE_LIVE_AGENTS:
        print(f"🤖 [{run_id[:8]}] Running LIVE Gemini agents for {scenario}")
        from agents.orchestrator_live import run_live_scenario
        await run_live_scenario(run_id, scenario, set_run_status)
    else:
        print(f"📜 [{run_id[:8]}] Running HARDCODED scenario for {scenario}")
        await run_hardcoded_scenario(run_id, scenario)


# ── Hardcoded runner (Phase 1 fallback) ──────────────────────────────────

async def run_hardcoded_scenario(run_id: str, scenario: ScenarioType) -> None:
    """
    Publishes all hardcoded events to Redis on schedule.
    Used when GEMINI_API_KEY is not set or USE_LIVE_AGENTS=False.
    """
    steps = get_hardcoded_steps(scenario)
    start_time = asyncio.get_event_loop().time()

    for step in steps:
        target_time = start_time + (step["delay_ms"] / 1000.0)
        now = asyncio.get_event_loop().time()
        wait = target_time - now
        if wait > 0:
            await asyncio.sleep(wait)
        await redis_client.publish(run_id, step["event"])

    set_run_status(run_id, RunStatus.AWAITING_APPROVAL)
    await redis_client.set_run_state(run_id, _runs[run_id])


# ── Execution cascade (shared by both modes) ─────────────────────────────

async def run_execution_cascade(run_id: str) -> None:
    """
    Background task: fires execution events after human approval.
    Same for both live and hardcoded modes.
    """
    set_run_status(run_id, RunStatus.APPROVED)

    steps = get_execution_steps()
    start_time = asyncio.get_event_loop().time()

    for step in steps:
        target_time = start_time + (step["delay_ms"] / 1000.0)
        now = asyncio.get_event_loop().time()
        wait = target_time - now
        if wait > 0:
            await asyncio.sleep(wait)
        await redis_client.publish(run_id, step["event"])

    set_run_status(run_id, RunStatus.COMPLETE)
    await redis_client.set_run_state(run_id, _runs[run_id])
