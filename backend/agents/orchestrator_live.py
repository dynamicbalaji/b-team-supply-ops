"""
agents/orchestrator_live.py — LangGraph Helper Functions & Historical Archive
═══════════════════════════════════════════════════════════════════════════════

ROLE IN LANGGRAPH ARCHITECTURE
──────────────────────────────
This module provides shared helper functions used by `graph/orchestrator_graph.py`
inside individual LangGraph nodes. It is NOT an orchestration module — it contains
no control flow, no scheduling, and no multi-agent coordination.

Helpers provided:
  • _orc_msg(run_id, text, ts)      — Publish a MessageEvent for the Orchestrator
  • _phase(run_id, phase, status)    — Publish a PhaseEvent (phase change)
  • _map(run_id, status, color, route) — Publish a MapUpdateEvent (UI map update)
  • _safe_context_summary(ctx)       — Strip non-serialisable values for Redis storage

All helpers are used **inside LangGraph nodes**, which call them as needed
for event emission. They are pure event publishers — no orchestration.

════════════════════════════════════════════════════════════════════════════════
ARCHIVED CODE — NEVER CALLED
════════════════════════════════════════════════════════════════════════════════

_ARCHIVED_run_live_scenario()
─────────────────────────────
This is the original hand-written multi-agent orchestration loop predating LangGraph.
It is preserved below for historical reference only and is NEVER called in live mode.

Its asyncio.gather(logistics_agent.run(), procurement_agent.run()) has been
superseded by the LangGraph edge sequence in graph/orchestrator_graph.py:
    round1_logistics → round1_procurement

LangGraph's sequential edge execution replaces the explicit asyncio coordination.
This archive demonstrates the evolution from hand-written scheduling to
declarative graph edges.

════════════════════════════════════════════════════════════════════════════════
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


# ─────────────────────────────────────────────────────────────────────────
# Helper 1: Publish an Orchestrator message event
# ─────────────────────────────────────────────────────────────────────────

async def _orc_msg(run_id: str, text: str, ts: str) -> None:
    """
    Publish a MessageEvent as if from the Orchestrator.

    Used by graph/orchestrator_graph.py nodes to emit orchestrator narration
    to the SSE stream (e.g., "Crisis P0: SC-2024-8891 blocked at Long Beach").

    Args:
        run_id: Run identifier (Redis channel).
        text: Message text.
        ts: Timestamp string (e.g., "0.0s").
    """
    await redis_client.publish(run_id, MessageEvent(
        agent=AgentId.ORCHESTRATOR,
        from_label="ORCHESTRATOR",
        to_label="→ ALL",
        timestamp=ts,
        css_class="orc",
        text=text,
        tools=[],
    ).model_dump())


# ─────────────────────────────────────────────────────────────────────────
# Helper 2: Publish a phase change event
# ─────────────────────────────────────────────────────────────────────────

async def _phase(run_id: str, phase: int, status: str) -> None:
    """
    Publish a PhaseEvent to signal phase transitions.

    Used by graph/orchestrator_graph.py to emit phase changes
    (e.g., phase=0→1 "active", phase=1→"done").

    Args:
        run_id: Run identifier (Redis channel).
        phase: Phase number (0-5).
        status: "active" or "done".
    """
    await redis_client.publish(run_id, PhaseEvent(
        phase=phase, status=status
    ).model_dump())


# ─────────────────────────────────────────────────────────────────────────
# Helper 3: Publish a map update event
# ─────────────────────────────────────────────────────────────────────────

async def _map(run_id: str, status: str, color: str, route: str | None = None) -> None:
    """
    Publish a MapUpdateEvent to update the UI map display.

    Used by graph/orchestrator_graph.py to update the supply chain map
    (e.g., status="AGENTS ACTIVE", color="#ffb340").

    Args:
        run_id: Run identifier (Redis channel).
        status: Status text (e.g., "AGENTS ACTIVE").
        color: Hex color code (e.g., "#ffb340").
        route: Optional route description (e.g., "Evaluating routes").
    """
    await redis_client.publish(run_id, MapUpdateEvent(
        status=status, status_color=color, route=route
    ).model_dump())


# ─────────────────────────────────────────────────────────────────────────
# Helper 4: Sanitise context for Redis storage
# ─────────────────────────────────────────────────────────────────────────

def _safe_context_summary(run_context: dict) -> dict:
    """
    Strip non-serialisable objects from run context for Redis storage.

    LangGraph nodes collect agent outputs in run_context. Before persisting
    to Redis, we filter to only JSON-serialisable types.

    Args:
        run_context: Dict of agent outputs (may contain objects).

    Returns:
        Dict with only str, int, float, bool, list, dict, None values.
    """
    return {
        agent: {
            k: v for k, v in data.items()
            if isinstance(v, (str, int, float, bool, list, dict, type(None)))
        }
        for agent, data in run_context.items()
        if isinstance(data, dict)
    }


# ════════════════════════════════════════════════════════════════════════════════
# ARCHIVED: _ARCHIVED_run_live_scenario()
# ════════════════════════════════════════════════════════════════════════════════
#
# Original hand-written orchestration loop (pre-LangGraph).
# Preserved for historical reference only.
# Never called in live mode — use graph/orchestrator_graph.py instead.
#
# This code demonstrates how multi-agent coordination was done before LangGraph:
# explicit asyncio.gather() calls, manual state threading, and hardcoded
# control flow. All of this is now expressed as LangGraph edges.

async def _ARCHIVED_run_live_scenario(
    run_id: str,
    scenario: ScenarioType,
    set_status_fn,           # orchestrator.set_run_status callback
) -> None:
    """
    [ARCHIVED] Full live Gemini multi-agent workflow (pre-LangGraph).

    This is the original orchestration loop that coordinated agents
    via explicit asyncio.gather() and manual state threading.
    It has been superseded by the declarative LangGraph _SCENARIO_GRAPH
    in graph/orchestrator_graph.py.

    ╔════════════════════════════════════════════════════════════════╗
    ║ THIS FUNCTION IS NEVER CALLED. SEE graph/orchestrator_graph.py ║
    ║ FOR THE CURRENT IMPLEMENTATION.                                ║
    ╚════════════════════════════════════════════════════════════════╝

    Original control flow:
      Phase 0→1: Orchestrator broadcasts
      Phase 1: asyncio.gather(logistics, procurement)  ← REPLACED BY LANGGRAPH EDGES
      Phase 2: Finance challenges Logistics
      Phase 2b: Logistics revises
      Phase 3: Sales negotiates SLA
      Phase 4: Risk fires Devil's Advocate
      Phase 5: Finance proposes consensus
      Phase 3 awaiting approval: Awaiting human approval

    set_status_fn: callable(run_id, RunStatus) — updates in-memory run state
    """
    sc = SCENARIO_DEFINITIONS[scenario]
    run_context: dict = {}
    start = time.time()

    try:
        # ════════════════════════════════════════════════════════════════
        # PHASE 0 → 1: Orchestrator broadcasts the crisis
        # ════════════════════════════════════════════════════════════════
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

        # ════════════════════════════════════════════════════════════════
        # ROUND 1 (PARALLEL): Logistics + Procurement
        # ════════════════════════════════════════════════════════════════
        # ARCHIVED PATTERN: Both run concurrently via asyncio.gather().
        # REPLACED BY: LangGraph edge round1_logistics → round1_procurement
        #
        # LangGraph's sequential edges provide the same coordination
        # without explicit asyncio primitives at the orchestration level.

        await asyncio.gather(
            logistics_agent.run(run_id, scenario, run_context, start),
            procurement_agent.run(run_id, scenario, run_context, start),
        )

        await _phase(run_id, 1, "done")
        await _phase(run_id, 2, "active")

        # ════════════════════════════════════════════════════════════════
        # ROUND 2: Finance challenges Logistics
        # ════════════════════════════════════════════════════════════════

        await finance_agent.run(run_id, scenario, run_context, start)

        # ════════════════════════════════════════════════════════════════
        # ROUND 2b: Logistics revises after Finance challenge
        # ════════════════════════════════════════════════════════════════

        finance_out = run_context.get("finance", {})
        customs_surcharge = finance_out.get("customs_surcharge", 50_000)
        challenge_text = finance_out.get("challenge_text", "Customs surcharge applies.")

        await logistics_agent.revise(
            run_id, scenario, run_context, start,
            challenge=challenge_text,
            customs_surcharge=customs_surcharge,
        )

        # ════════════════════════════════════════════════════════════════
        # ROUND 3: Sales negotiates SLA
        # (runs while Finance is still digesting the revision)
        # ════════════════════════════════════════════════════════════════

        await sales_agent.run(run_id, scenario, run_context, start)

        # ════════════════════════════════════════════════════════════════
        # ROUND 4: Risk Agent fires Devil's Advocate
        # The single most important moment — fires AFTER consensus
        # ════════════════════════════════════════════════════════════════

        await risk_agent.run(run_id, scenario, run_context, start)

        # ════════════════════════════════════════════════════════════════
        # ROUND 5: Finance absorbs risk contingency + proposes approval
        # ════════════════════════════════════════════════════════════════

        await finance_agent.propose_consensus(
            run_id, scenario, run_context, start,
            reserve_usd=20_000,
        )

        # Procurement acknowledges and stands down
        await procurement_agent.acknowledge(run_id, run_context, start)

        # ════════════════════════════════════════════════════════════════
        # PHASE 3: Awaiting human approval
        # ════════════════════════════════════════════════════════════════

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

        safe_ctx = _safe_context_summary(run_context)
        await redis_client.set_run_state(run_id, {
            "run_id":   run_id,
            "scenario": scenario,
            "status":   RunStatus.AWAITING_APPROVAL,
            "context":  safe_ctx,
        })

        # ── Phase 3: Persist run context + new episodic memory ────────────
        try:
            import turso_client
            if turso_client.is_configured():
                # 1. Save full run context (enables post-run analytics)
                await turso_client.save_run_context(run_id, run_context)

                # 2. Write this run as a new episodic memory record
                #    so future runs can recall it via memory_recall()
                logistics = run_context.get("logistics", {})
                finance   = run_context.get("finance", {})
                if logistics.get("cost_usd") and finance.get("mc_result"):
                    import time as _time
                    mc    = finance["mc_result"]
                    saved = sc.penalty_usd - logistics.get("cost_usd", 0)
                    await turso_client.save_memory(
                        memory_key     = f"run_{run_id[:8]}_{scenario.value}",
                        scenario_type  = scenario.value,
                        date_label     = _time.strftime("%B %Y"),
                        crisis         = sc.crisis_title,
                        decision       = f"Hybrid route — ${logistics['cost_usd'] // 1000}K / {logistics.get('transit_hours', 36)}h",
                        outcome        = f"Resolved in {elapsed(start)}. MC confidence {int(mc.get('confidence_interval', 0.94) * 100)}%.",
                        cost_usd       = logistics["cost_usd"],
                        saved_usd      = max(saved, 0),
                        key_learning   = f"Hybrid beat air-only by ~${finance.get('customs_surcharge', 0) // 1000}K customs surcharge.",
                        confidence     = mc.get("confidence_interval", 0.94),
                    )
        except Exception as mem_exc:
            print(f"   [orchestrator] TursoDB persist skipped: {mem_exc}")

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
