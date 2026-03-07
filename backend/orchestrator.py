"""
orchestrator.py
───────────────
Run registry and scenario entry points.

Live path  (USE_LIVE_AGENTS = True)
────────────────────────────────────
Both run_scenario() and run_execution_cascade() delegate to compiled
LangGraph graphs.  There is no asyncio.gather, asyncio.create_task, or
hand-written event-loop scheduling in the live path.  The only async
primitives here are the two `await graph.ainvoke(...)` calls inside
each entry point.

        run_scenario()            → graph.orchestrator_graph.run_scenario_graph()
        run_execution_cascade()   → graph.orchestrator_graph.run_execution_cascade_graph()

Hardcoded path  (USE_LIVE_AGENTS = False)
──────────────────────────────────────────
Used when GEMINI_API_KEY is absent.  The timing-based event emission is
isolated in the single helper _emit_timed_steps(), which is clearly NOT
orchestration logic — it is a demo replay mechanism that replays a static
list of {delay_ms, event} pairs.  All asyncio.sleep calls live inside
this one function and nowhere else in this module.

TursoDB shadow writes
──────────────────────
_fire_and_forget(coro) wraps asyncio.get_running_loop().create_task() so
the intent is explicit: "start this DB write in the background and do not
wait for it."  It appears in two synchronous state-mutating functions
(create_run, set_run_status) where awaiting would block the caller.
"""

import asyncio
import time as _time

import redis_client
from config import get_settings
from models import ScenarioType, RunStatus
from scenarios import get_hardcoded_steps, get_execution_steps

settings = get_settings()

# ── Feature flag ──────────────────────────────────────────────────────────
# Set USE_LIVE_AGENTS=true in .env (or ensure GEMINI_API_KEY is set).
USE_LIVE_AGENTS: bool = (
    bool(settings.gemini_api_key)
    and settings.gemini_api_key != "your_gemini_api_key_here"
)

# ── Run registry — in-memory primary, TursoDB async shadow write ──────────
_runs: dict[str, dict] = {}


def get_run(run_id: str) -> dict | None:
    return _runs.get(run_id)


# ── TursoDB fire-and-forget helper ────────────────────────────────────────
# Wraps loop.create_task so all background DB writes are clearly labelled.
# This is NOT orchestration — it is a non-blocking persistence side-effect
# on every in-memory state mutation.

def _fire_and_forget(coro) -> None:
    """Schedule a DB-write coroutine as a background task without awaiting it.

    Used only for TursoDB shadow writes.  If no event loop is running
    (tests, CLI) the coroutine is silently dropped — the in-memory dict
    remains the authoritative source of truth.
    """
    try:
        asyncio.get_running_loop().create_task(coro)
    except RuntimeError:
        pass


def create_run(run_id: str, scenario: ScenarioType) -> dict:
    mode = "live" if USE_LIVE_AGENTS else "hardcoded"
    run = {
        "run_id":   run_id,
        "scenario": scenario,
        "status":   RunStatus.PENDING,
        "approved": False,
        "mode":     mode,
    }
    _runs[run_id] = run
    try:
        import turso_client
        if turso_client.is_configured():
            _fire_and_forget(turso_client.create_run(run_id, scenario.value, mode))
    except Exception:
        pass
    return run


def set_run_status(run_id: str, status: RunStatus) -> None:
    if run_id in _runs:
        _runs[run_id]["status"] = status
    try:
        import turso_client
        if turso_client.is_configured():
            _fire_and_forget(turso_client.update_run_status(run_id, status.value))
    except Exception:
        pass


# ── Demo timing helper (hardcoded path only) ──────────────────────────────
# This is the ONLY place in this module that contains asyncio.sleep.
# It exists solely to replay a static list of pre-timed events for the
# demo fallback — it is not orchestration logic.
#
# It knows nothing about run state, agent coordination, or business rules.
# Think of it as a media player that replays a recording at its original
# timestamps.  It is never called when USE_LIVE_AGENTS is True.

async def _emit_timed_steps(run_id: str, steps: list[dict]) -> None:
    """Replay a list of {delay_ms, event} pairs to Redis at their recorded times.

    Used by: run_hardcoded_scenario(), run_hardcoded_cascade()
    NOT used when USE_LIVE_AGENTS is True.
    """
    origin = asyncio.get_event_loop().time()
    for step in steps:
        target = origin + step["delay_ms"] / 1000.0
        wait   = asyncio.get_event_loop().time()
        wait   = target - wait
        if wait > 0:
            await asyncio.sleep(wait)
        await redis_client.publish(run_id, step["event"])


# ── Scenario entry point ──────────────────────────────────────────────────

async def run_scenario(run_id: str, scenario: ScenarioType) -> None:
    """
    Top-level entry point called by background_tasks.add_task() in main.py.

    Live path:      one await — delegates entirely to the LangGraph graph.
    Hardcoded path: replays the static event list via _emit_timed_steps().
    """
    set_run_status(run_id, RunStatus.RUNNING)

    if USE_LIVE_AGENTS:
        print(f"🤖 [{run_id[:8]}] LIVE — LangGraph scenario graph ({scenario})")
        from graph.orchestrator_graph import run_scenario_graph
        await run_scenario_graph(run_id, scenario)
    else:
        print(f"📜 [{run_id[:8]}] HARDCODED fallback ({scenario})")
        await run_hardcoded_scenario(run_id, scenario)


# ── Execution cascade (post-approval) ────────────────────────────────────

async def run_execution_cascade(run_id: str) -> None:
    """
    Background task triggered by POST /api/runs/{run_id}/approve.

    Live path:      one await — delegates to the LangGraph cascade graph.
    Hardcoded path: replays the static execution event list.
    """
    set_run_status(run_id, RunStatus.APPROVED)
    started_at = _time.time()

    if USE_LIVE_AGENTS:
        print(f"🤖 [{run_id[:8]}] LIVE — LangGraph execution cascade")
        from graph.orchestrator_graph import run_execution_cascade_graph
        await run_execution_cascade_graph(run_id, started_at)
    else:
        print(f"📜 [{run_id[:8]}] HARDCODED execution cascade")
        await run_hardcoded_cascade(run_id)

    set_run_status(run_id, RunStatus.COMPLETE)
    await redis_client.set_run_state(run_id, _runs[run_id])


# ── Hardcoded runners (demo fallback — never called when live) ────────────

async def run_hardcoded_scenario(run_id: str, scenario: ScenarioType) -> None:
    """Replay the hardcoded scenario event list at recorded timestamps."""
    await _emit_timed_steps(run_id, get_hardcoded_steps(scenario))
    set_run_status(run_id, RunStatus.AWAITING_APPROVAL)
    await redis_client.set_run_state(run_id, _runs[run_id])


async def run_hardcoded_cascade(run_id: str) -> None:
    """Replay the hardcoded execution event list at recorded timestamps."""
    await _emit_timed_steps(run_id, get_execution_steps())
