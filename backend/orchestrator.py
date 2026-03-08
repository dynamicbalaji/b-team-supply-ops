"""
orchestrator.py — Scenario Entry Points & Run Registry
════════════════════════════════════════════════════════

ROLE IN LANGGRAPH ARCHITECTURE
──────────────────────────────
This module is a thin adapter that:

  1. Manages the in-memory run registry (primary source of truth)
  2. Routes requests to LangGraph graphs (live path) or hardcoded replay (demo path)
  3. Provides two entry points: run_scenario() and run_execution_cascade()

The actual orchestration logic is NOT here — it lives in `graph/orchestrator_graph.py`
and the five agent subgraphs in `graph/*_agent_graph.py`.

ZERO ORCHESTRATION LOGIC IN THIS FILE
──────────────────────────────────────
There are NO asyncio.gather(), asyncio.sleep(), or task scheduling calls
that control multi-agent behavior. The only asyncio primitives are:

  • await graph.ainvoke(state)  — delegate entirely to LangGraph
  • await redis_client.publish() — emit SSE events (simple I/O)
  • await turso_client.*()       — persist state to TursoDB (fire-and-forget)

Live Path (USE_LIVE_AGENTS = True)
──────────────────────────────────
run_scenario()
    │
    └─► from graph.orchestrator_graph import run_scenario_graph
        await run_scenario_graph(run_id, scenario)
        │
        └─► [LangGraph _SCENARIO_GRAPH is invoked]
            phase0_broadcast → round1_logistics → ... → awaiting_approval → END
            (All edges defined as LangGraph control flow, not asyncio primitives)

run_execution_cascade()
    │
    └─► from graph.orchestrator_graph import run_execution_cascade_graph
        await run_execution_cascade_graph(run_id)
        │
        └─► [LangGraph _CASCADE_GRAPH is invoked]
            exec_phase_transition → exec_logistics_confirm → ... → END

Hardcoded Fallback Path (USE_LIVE_AGENTS = False)
──────────────────────────────────────────────────
Used only when Gemini API key is absent or invalid. Replays a static
event list at recorded timestamps. The timing logic (_emit_timed_steps)
is isolated so it is obviously NOT orchestration — it is demo replay.

run_scenario()
    │
    └─► run_hardcoded_scenario(run_id, scenario)
        │
        └─► _emit_timed_steps(run_id, get_hardcoded_steps(scenario))
            [For each recorded step: await asyncio.sleep(wait), await publish()]
            This is a media player that emits pre-recorded events, not a scheduler.

run_execution_cascade()
    │
    └─► run_hardcoded_cascade(run_id)
        │
        └─► _emit_timed_steps(run_id, get_execution_steps())
            [Same media player logic]

Run Registry
────────────
_runs: dict[str, dict]
  Primary in-memory store. TursoDB receives fire-and-forget async writes
  via _fire_and_forget(coro), which is NOT orchestration — it is background
  persistence.

TursoDB Fire-and-Forget Pattern
────────────────────────────────
When orchestrator.py mutates _runs state (create_run, set_run_status), it
also schedules a non-blocking DB write via asyncio.get_running_loop().create_task().
This is purely for durability, not coordination.

Called by:
  • create_run() — persist new run to TursoDB
  • set_run_status() — persist status changes to TursoDB

If no event loop is running (tests, CLI), the writes are silently dropped.
In-memory dict remains the authoritative source of truth.
"""

import asyncio
import time as _time

import redis_client
from config import get_settings
from models import ScenarioType, RunStatus
from scenarios import get_hardcoded_steps, get_execution_steps

settings = get_settings()

# ─────────────────────────────────────────────────────────────────────────
# Feature Flag: Live LangGraph vs. Hardcoded Replay
# ─────────────────────────────────────────────────────────────────────────
#
# If Gemini API key is set and not the placeholder, use LangGraph.
# Otherwise, fall back to Phase 1 hardcoded event replay (demo mode).

USE_LIVE_AGENTS: bool = (
    bool(settings.gemini_api_key)
    and settings.gemini_api_key != "your_gemini_api_key_here"
)


# ─────────────────────────────────────────────────────────────────────────
# Run Registry — In-Memory Primary, TursoDB Async Shadow Write
# ─────────────────────────────────────────────────────────────────────────

_runs: dict[str, dict] = {}


def get_run(run_id: str) -> dict | None:
    """Fetch run state from in-memory registry."""
    return _runs.get(run_id)


# ─────────────────────────────────────────────────────────────────────────
# TursoDB Fire-and-Forget Helper
# ─────────────────────────────────────────────────────────────────────────
#
# Not orchestration — purely for non-blocking DB persistence.
# Wraps asyncio.get_running_loop().create_task() so intent is explicit.

def _fire_and_forget(coro) -> None:
    """
    Schedule a database coroutine as a background task without awaiting.

    Used only for TursoDB shadow writes of in-memory state mutations.
    If no event loop is running (tests, CLI), the coroutine is silently
    dropped — the in-memory dict remains the authoritative source.

    Args:
        coro: Awaitable (e.g., turso_client.create_run(...))
    """
    try:
        asyncio.get_running_loop().create_task(coro)
    except RuntimeError:
        # No event loop running; this is fine in tests/CLI
        pass


def create_run(run_id: str, scenario: ScenarioType) -> dict:
    """
    Create a new run in the in-memory registry and shadow-write to TursoDB.

    Args:
        run_id: Unique run identifier (UUID string).
        scenario: ScenarioType enum.

    Returns:
        The new run dict.
    """
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
    """
    Update run status in the in-memory registry and shadow-write to TursoDB.

    When status is APPROVED, also flips the approved flag in both the
    in-memory dict and the TursoDB runs.approved column.

    Args:
        run_id: Run identifier.
        status: New RunStatus.
    """
    if run_id in _runs:
        _runs[run_id]["status"] = status
        if status == RunStatus.APPROVED:
            _runs[run_id]["approved"] = True
    try:
        import turso_client
        if turso_client.is_configured():
            _fire_and_forget(turso_client.update_run_status(run_id, status.value))
            if status == RunStatus.APPROVED:
                _fire_and_forget(turso_client.set_run_approved(run_id))
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────
# Demo Replay Helper (Hardcoded Path Only)
# ─────────────────────────────────────────────────────────────────────────
#
# MEDIA PLAYER, NOT ORCHESTRATION
#
# This is the ONLY place in this module that contains asyncio.sleep.
# It exists solely to replay a static list of pre-timed events for the
# Phase 1 demo fallback — it has nothing to do with agent orchestration,
# multi-agent coordination, or business logic.
#
# It knows nothing about run state mutations, agent behavior, or crisis rules.
# Think of it as pressing play on a recording: wait N milliseconds, emit event.
#
# Never called when USE_LIVE_AGENTS is True.

async def _emit_timed_steps(run_id: str, steps: list[dict]) -> None:
    """
    Replay a list of {delay_ms, event} pairs to Redis at their recorded times.

    This is a media player for the Phase 1 demo fallback. It has no knowledge
    of orchestration, agent state, or business rules. It simply waits and
    replays pre-recorded events.

    Args:
        run_id: Run identifier (used as Redis channel).
        steps: List of dicts, each with keys:
            - delay_ms: milliseconds after scenario start
            - event: dict (SSE event payload)

    Used by:
        run_hardcoded_scenario()
        run_hardcoded_cascade()

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


# ─────────────────────────────────────────────────────────────────────────
# Scenario Entry Point
# ─────────────────────────────────────────────────────────────────────────

async def run_scenario(run_id: str, scenario: ScenarioType) -> None:
    """
    Top-level entry point for scenario execution (Phase 1-3).

    Called by FastAPI background_tasks.add_task() in main.py.

    Live path:      Delegates entirely to LangGraph's _SCENARIO_GRAPH.
                    One await: await run_scenario_graph(run_id, scenario)
                    No orchestration code here.

    Hardcoded path: Replays Phase 1 event list via _emit_timed_steps().
                    Only runs if Gemini API key is absent/invalid.

    Args:
        run_id: Unique run identifier.
        scenario: ScenarioType enum.
    """
    set_run_status(run_id, RunStatus.RUNNING)

    if USE_LIVE_AGENTS:
        print(f"🤖 [{run_id[:8]}] LIVE — LangGraph scenario graph ({scenario})")
        from graph.orchestrator_graph import run_scenario_graph
        await run_scenario_graph(run_id, scenario)
    else:
        print(f"📜 [{run_id[:8]}] HARDCODED fallback ({scenario})")
        await run_hardcoded_scenario(run_id, scenario)


# ─────────────────────────────────────────────────────────────────────────
# Execution Cascade (Post-Approval, Phase 4-5)
# ─────────────────────────────────────────────────────────────────────────

async def run_execution_cascade(run_id: str, scenario: ScenarioType | None = None) -> None:
    """
    Execute the post-approval cascade (Phase 4-5).

    Called by FastAPI background_tasks.add_task() after POST /api/runs/{run_id}/approve.

    Live path:      Delegates entirely to LangGraph's _CASCADE_GRAPH.
                    One await: await run_execution_cascade_graph(run_id)
                    No orchestration code here.

    Hardcoded path: Replays Phase 1 execution event list.
                    Only runs if Gemini API key is absent/invalid.

    Args:
        run_id: Unique run identifier.
    """
    set_run_status(run_id, RunStatus.APPROVED)
    started_at = _time.time()

    if USE_LIVE_AGENTS:
        print(f"🤖 [{run_id[:8]}] LIVE — LangGraph execution cascade")
        from graph.orchestrator_graph import run_execution_cascade_graph
        await run_execution_cascade_graph(run_id, started_at)
    else:
        print(f"📜 [{run_id[:8]}] HARDCODED execution cascade")
        run_scenario = _runs.get(run_id, {}).get("scenario", ScenarioType.PORT_STRIKE)
        await run_hardcoded_cascade(run_id, run_scenario)

    set_run_status(run_id, RunStatus.COMPLETE)
    await redis_client.set_run_state(run_id, _runs[run_id])


# ─────────────────────────────────────────────────────────────────────────
# Hardcoded Runners (Demo Fallback — Never Called When Live)
# ─────────────────────────────────────────────────────────────────────────

async def run_hardcoded_scenario(run_id: str, scenario: ScenarioType) -> None:
    """
    Replay Phase 1 scenario event list at recorded timestamps.

    This is only called when Gemini API key is absent/invalid.
    It replays a pre-recorded event sequence so the frontend UI looks
    identical to the live Gemini version.

    Args:
        run_id: Run identifier.
        scenario: ScenarioType enum.
    """
    await _emit_timed_steps(run_id, get_hardcoded_steps(scenario))
    set_run_status(run_id, RunStatus.AWAITING_APPROVAL)
    await redis_client.set_run_state(run_id, _runs[run_id])


async def run_hardcoded_cascade(run_id: str, scenario: ScenarioType = ScenarioType.PORT_STRIKE) -> None:
    """
    Replay Phase 1 execution event list at recorded timestamps.

    This is only called when Gemini API key is absent/invalid.

    Args:
        run_id: Run identifier.
        scenario: ScenarioType to generate scenario-specific messages.
    """
    await _emit_timed_steps(run_id, get_execution_steps(scenario))
