"""
agents/orchestrator_live.py
────────────────────────────
Live Gemini orchestrator for Phase 2.

Replaces run_hardcoded_scenario() with a real multi-agent workflow:

  Round 1 (parallel):  Logistics + Procurement run simultaneously
  Round 2 (sequential): Finance reads Logistics output → challenges it
  Round 2b:             Logistics revises after Finance challenge
  Round 2c:             Finance + Logistics reach consensus
  Round 3:              Sales negotiates SLA (reads Finance consensus)
  Round 4:              Risk Agent fires Devil's Advocate AFTER all consensus
  Round 5:              Finance absorbs risk → proposes final approval
  Human:                Approval required event published → judge clicks APPROVE

The run_context dict is the shared memory between agents.
It is NOT persisted in Phase 2 (Phase 3 adds TursoDB).

Timing guardrails:
  - Each round has a max_wait_seconds before we fall back to a shorter prompt
  - This prevents Gemini latency from killing the demo pace
  - Total expected time: 45–90 seconds of real Gemini streaming
"""

import asyncio
import time
import json

import redis_client
import agents.logistics    as logistics_agent
import agents.finance      as finance_agent
import agents.procurement  as procurement_agent
import agents.sales        as sales_agent
import agents.risk         as risk_agent

from models import (
    AgentId, AgentStatus, ScenarioType, RunStatus,
    PhaseEvent, AgentStateEvent, MessageEvent,
    ApprovalRequiredEvent, MapUpdateEvent,
)
from scenarios import SCENARIO_DEFINITIONS
from agents.base import publish_state, elapsed


# ── Publish helper for orchestrator's own messages ────────────────────────

async def _orc_msg(run_id: str, text: str, ts: str) -> None:
    await redis_client.publish(run_id, MessageEvent(
        agent=AgentId.ORCHESTRATOR,
        from_label="ORCHESTRATOR",
        to_label="→ ALL",
        timestamp=ts,
        css_class="orc",
        text=text,
        tools=[],
    ).model_dump())


async def _phase(run_id: str, phase: int, status: str) -> None:
    await redis_client.publish(run_id, PhaseEvent(
        phase=phase, status=status
    ).model_dump())


async def _map(run_id: str, status: str, color: str, route: str | None = None) -> None:
    await redis_client.publish(run_id, MapUpdateEvent(
        status=status, status_color=color, route=route
    ).model_dump())


# ── Main live scenario runner ─────────────────────────────────────────────

async def run_live_scenario(
    run_id: str,
    scenario: ScenarioType,
    set_status_fn,           # orchestrator.set_run_status callback
) -> None:
    """
    Full live Gemini multi-agent workflow.
    Called as a FastAPI background task.

    set_status_fn: callable(run_id, RunStatus) — updates in-memory run state
    """
    sc = SCENARIO_DEFINITIONS[scenario]
    run_context: dict = {}
    start = time.time()

    try:
        # ════════════════════════════════════════════════
        # PHASE 0 → 1: Orchestrator broadcasts the crisis
        # ════════════════════════════════════════════════
        await _phase(run_id, 0, "done")
        await _phase(run_id, 1, "active")

        await _orc_msg(
            run_id,
            f"Crisis P0: SC-2024-8891 blocked at Long Beach. "
            f"Budget cap ${sc.budget_cap_usd // 1000}K. "
            f"Deadline {sc.deadline_hours}h. Begin parallel evaluation.",
            elapsed(start),
        )
        await _map(run_id, "AGENTS ACTIVE", "#ffb340", "Evaluating routes")

        # ════════════════════════════════════════════════
        # ROUND 1 (PARALLEL): Logistics + Procurement
        # ════════════════════════════════════════════════
        # Both run concurrently — their tool calls and streaming happen in parallel
        # The SSE queue serialises them FIFO, so browser sees interleaved tokens

        await asyncio.gather(
            logistics_agent.run(run_id, scenario, run_context, start),
            procurement_agent.run(run_id, scenario, run_context, start),
        )

        await _phase(run_id, 1, "done")
        await _phase(run_id, 2, "active")

        # ════════════════════════════════════════════════
        # ROUND 2: Finance challenges Logistics
        # ════════════════════════════════════════════════

        await finance_agent.run(run_id, scenario, run_context, start)

        # ════════════════════════════════════════════════
        # ROUND 2b: Logistics revises after Finance challenge
        # ════════════════════════════════════════════════

        finance_out = run_context.get("finance", {})
        customs_surcharge = finance_out.get("customs_surcharge", 50_000)
        challenge_text = finance_out.get("challenge_text", "Customs surcharge applies.")

        await logistics_agent.revise(
            run_id, scenario, run_context, start,
            challenge=challenge_text,
            customs_surcharge=customs_surcharge,
        )

        # ════════════════════════════════════════════════
        # ROUND 3: Sales negotiates SLA
        # (runs while Finance is still digesting the revision)
        # ════════════════════════════════════════════════

        await sales_agent.run(run_id, scenario, run_context, start)

        # ════════════════════════════════════════════════
        # ROUND 4: Risk Agent fires Devil's Advocate
        # The single most important moment — fires AFTER consensus
        # ════════════════════════════════════════════════

        await risk_agent.run(run_id, scenario, run_context, start)

        # ════════════════════════════════════════════════
        # ROUND 5: Finance absorbs risk contingency + proposes approval
        # ════════════════════════════════════════════════

        await finance_agent.propose_consensus(
            run_id, scenario, run_context, start,
            reserve_usd=20_000,
        )

        # Procurement acknowledges and stands down
        await procurement_agent.acknowledge(run_id, run_context, start)

        # ════════════════════════════════════════════════
        # PHASE 3: Awaiting human approval
        # ════════════════════════════════════════════════

        await _phase(run_id, 2, "done")
        await _phase(run_id, 3, "active")

        finance_final = run_context.get("finance", {})
        mc = finance_final.get("mc_result", {})
        hybrid_cost = finance_final.get("hybrid_cost", 253_000)
        confidence = mc.get("confidence_interval", 0.94)

        await redis_client.publish(run_id, ApprovalRequiredEvent(
            option="hybrid",
            label="Hybrid Route — 60% Air / 40% Sea",
            cost_usd=hybrid_cost,
            reserve_usd=20_000,
            delivery_hours=run_context.get("logistics", {}).get("transit_hours", 36),
            confidence=confidence,
            detail=(
                f"${hybrid_cost // 1000}K + $20K reserve · "
                f"{run_context.get('logistics', {}).get('transit_hours', 36)}h delivery · "
                f"Backup trigger H20 · {sc.customer}: ✓ · "
                f"Confidence: {int(confidence * 100)}%"
            ),
        ).model_dump())

        await _map(run_id, "AWAITING APPROVAL", "#ffb340")

        set_status_fn(run_id, RunStatus.AWAITING_APPROVAL)
        await redis_client.set_run_state(run_id, {
            "run_id":   run_id,
            "scenario": scenario,
            "status":   RunStatus.AWAITING_APPROVAL,
            "context":  _safe_context_summary(run_context),
        })

    except Exception as e:
        print(f"❌ Live scenario error for {run_id}: {e}")
        import traceback
        traceback.print_exc()
        # Publish error event so frontend doesn't hang silently
        await redis_client.publish(run_id, {
            "type":    "error",
            "message": f"Scenario failed: {str(e)[:200]}",
        })
        set_status_fn(run_id, RunStatus.FAILED)


def _safe_context_summary(run_context: dict) -> dict:
    """Strip non-serialisable objects for Redis storage."""
    return {
        agent: {
            k: v for k, v in data.items()
            if isinstance(v, (str, int, float, bool, list, dict, type(None)))
        }
        for agent, data in run_context.items()
        if isinstance(data, dict)
    }
