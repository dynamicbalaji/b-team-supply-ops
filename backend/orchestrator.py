"""
orchestrator.py
───────────────
Phase 1: Hardcoded scenario runner.

Reads the ordered event steps from scenarios.py and publishes each one
to Redis at the correct delay. Runs as a background asyncio task so the
POST /api/runs endpoint returns immediately while streaming continues.

Phase 2 will replace run_hardcoded_scenario() with run_live_scenario()
which calls Gemini for each agent — same publish interface, same Redis
queue, frontend notices zero difference.
"""

import asyncio
import redis_client
from models import ScenarioType, RunStatus
from scenarios import get_hardcoded_steps, get_execution_steps


# ── In-memory run registry (Phase 1) ────────────────────────────────────
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
    }
    _runs[run_id] = run
    return run


def set_run_status(run_id: str, status: RunStatus) -> None:
    if run_id in _runs:
        _runs[run_id]["status"] = status


# ── Main Phase 1 runner ──────────────────────────────────────────────────

async def run_hardcoded_scenario(run_id: str, scenario: ScenarioType) -> None:
    """
    Background task: publishes all hardcoded events to Redis on schedule.
    The SSE endpoint drains the queue and sends them to the browser.
    """
    set_run_status(run_id, RunStatus.RUNNING)

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

    # Persist state so reconnecting SSE clients know where we are
    await redis_client.set_run_state(run_id, _runs[run_id])


async def run_execution_cascade(run_id: str) -> None:
    """
    Background task: fires execution events after human approval.
    Called by POST /api/runs/{run_id}/approve.
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
