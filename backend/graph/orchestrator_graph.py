"""
graph/orchestrator_graph.py
───────────────────────────

LangGraph orchestrator for live scenarios.

This module expresses the multi-agent crisis-resolution flow from
agents/orchestrator_live.py as a LangGraph StateGraph over RunGraphState.

Phases / nodes:
  - phase0_broadcast
  - round1_parallel              (Logistics + Procurement)
  - round2_finance
  - round2b_logistics_revise
  - round3_sales
  - round4_risk
  - round5_finance_and_procurement_ack
  - awaiting_approval

Each node:
  - Reuses the existing agent modules (agents.logistics, agents.finance, ...)
  - Emits SSE events via redis_client.publish with the same shapes defined in
    models.py
  - Updates run_context in the shared graph state

The public entrypoint run_scenario_graph(run_id, scenario) is called from
orchestrator.run_scenario() when USE_LIVE_AGENTS is true.
"""

from __future__ import annotations

import time
from typing import Any

from langgraph.graph import StateGraph

import redis_client
import agents.logistics as logistics_agent
import agents.finance as finance_agent
import agents.procurement as procurement_agent
import agents.sales as sales_agent
import agents.risk as risk_agent

from models import (
    RunStatus,
    ScenarioType,
    ApprovalRequiredEvent,
)
from orchestrator import set_run_status
from scenarios import SCENARIO_DEFINITIONS
from agents.base import elapsed
from agents.orchestrator_live import _orc_msg, _phase, _map, _safe_context_summary
from .state import RunGraphState


async def _phase0_broadcast(state: RunGraphState) -> RunGraphState:
    """Phase 0→1: Orchestrator broadcasts the crisis and activates agents."""
    run_id = state["run_id"]
    scenario = state["scenario"]
    started_at = state.get("started_at") or time.time()
    state["started_at"] = started_at

    sc = SCENARIO_DEFINITIONS[scenario]

    await _phase(run_id, 0, "done")
    await _phase(run_id, 1, "active")

    await _orc_msg(
        run_id,
        (
            f"Crisis P0: SC-2024-8891 blocked at Long Beach. "
            f"Budget cap ${sc.budget_cap_usd // 1000}K. "
            f"Deadline {sc.deadline_hours}h. Begin parallel evaluation."
        ),
        elapsed(started_at),
    )
    await _map(run_id, "AGENTS ACTIVE", "#ffb340", "Evaluating routes")

    # High-level run status: running.
    set_run_status(run_id, RunStatus.RUNNING)
    state["status"] = RunStatus.RUNNING
    # Ensure run_context exists
    state.setdefault("run_context", {})
    return state


async def _round1_parallel(state: RunGraphState) -> RunGraphState:
    """
    Round 1: Logistics + Procurement.

    In the original implementation these run concurrently; here we call them
    sequentially while preserving their side effects (tool calls, SSE events,
    run_context updates). LangGraph will later allow us to introduce true
    parallelism at the graph level if desired.
    """
    run_id = state["run_id"]
    scenario = state["scenario"]
    started_at = state["started_at"]
    run_context = state.get("run_context", {})

    await logistics_agent.run(run_id, scenario, run_context, started_at)
    await procurement_agent.run(run_id, scenario, run_context, started_at)

    await _phase(run_id, 1, "done")
    await _phase(run_id, 2, "active")

    state["run_context"] = run_context
    return state


async def _round2_finance(state: RunGraphState) -> RunGraphState:
    """Round 2: Finance challenges Logistics."""
    run_id = state["run_id"]
    scenario = state["scenario"]
    started_at = state["started_at"]
    run_context = state.get("run_context", {})

    await finance_agent.run(run_id, scenario, run_context, started_at)

    state["run_context"] = run_context
    return state


async def _round2b_logistics_revise(state: RunGraphState) -> RunGraphState:
    """Round 2b: Logistics revises after Finance challenge."""
    run_id = state["run_id"]
    scenario = state["scenario"]
    started_at = state["started_at"]
    run_context = state.get("run_context", {})

    finance_out = run_context.get("finance", {})
    customs_surcharge = finance_out.get("customs_surcharge", 50_000)
    challenge_text = finance_out.get("challenge_text", "Customs surcharge applies.")

    await logistics_agent.revise(
        run_id,
        scenario,
        run_context,
        started_at,
        challenge=challenge_text,
        customs_surcharge=customs_surcharge,
    )

    state["run_context"] = run_context
    return state


async def _round3_sales(state: RunGraphState) -> RunGraphState:
    """Round 3: Sales negotiates SLA."""
    run_id = state["run_id"]
    scenario = state["scenario"]
    started_at = state["started_at"]
    run_context = state.get("run_context", {})

    await sales_agent.run(run_id, scenario, run_context, started_at)

    state["run_context"] = run_context
    return state


async def _round4_risk(state: RunGraphState) -> RunGraphState:
    """Round 4: Risk Agent fires Devil's Advocate."""
    run_id = state["run_id"]
    scenario = state["scenario"]
    started_at = state["started_at"]
    run_context = state.get("run_context", {})

    await risk_agent.run(run_id, scenario, run_context, started_at)

    state["run_context"] = run_context
    return state


async def _round5_finance_and_procurement_ack(
    state: RunGraphState,
) -> RunGraphState:
    """Round 5: Finance absorbs risk and Procurement acknowledges."""
    run_id = state["run_id"]
    scenario = state["scenario"]
    started_at = state["started_at"]
    run_context = state.get("run_context", {})

    await finance_agent.propose_consensus(
        run_id,
        scenario,
        run_context,
        started_at,
        reserve_usd=20_000,
    )

    await procurement_agent.acknowledge(run_id, run_context, started_at)

    state["run_context"] = run_context
    return state


async def _awaiting_approval(state: RunGraphState) -> RunGraphState:
    """
    Phase 3: Awaiting human approval.

    Publishes ApprovalRequiredEvent and persists run state + episodic memory
    via TursoDB, matching agents/orchestrator_live.run_live_scenario.
    """
    run_id = state["run_id"]
    scenario = state["scenario"]
    started_at = state["started_at"]
    run_context = state.get("run_context", {})
    sc = SCENARIO_DEFINITIONS[scenario]

    await _phase(run_id, 2, "done")
    await _phase(run_id, 3, "active")

    finance_final = run_context.get("finance", {})
    mc = finance_final.get("mc_result", {})
    hybrid_cost = finance_final.get("hybrid_cost", 253_000)
    confidence = mc.get("confidence_interval", 0.94)

    await redis_client.publish(
        run_id,
        ApprovalRequiredEvent(
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
        ).model_dump(),
    )

    await _map(run_id, "AWAITING APPROVAL", "#ffb340")

    # Update high-level run status.
    set_run_status(run_id, RunStatus.AWAITING_APPROVAL)
    state["status"] = RunStatus.AWAITING_APPROVAL

    safe_ctx = _safe_context_summary(run_context)
    await redis_client.set_run_state(
        run_id,
        {
            "run_id": run_id,
            "scenario": scenario,
            "status": RunStatus.AWAITING_APPROVAL,
            "context": safe_ctx,
        },
    )

    # Persist run context + episodic memory into TursoDB, if configured.
    try:
        import turso_client

        if turso_client.is_configured():
            await turso_client.save_run_context(run_id, run_context)

            logistics = run_context.get("logistics", {})
            finance = run_context.get("finance", {})
            if logistics.get("cost_usd") and finance.get("mc_result"):
                import time as _time

                mc_res = finance["mc_result"]
                saved = sc.penalty_usd - logistics.get("cost_usd", 0)
                await turso_client.save_memory(
                    memory_key=f"run_{run_id[:8]}_{scenario.value}",
                    scenario_type=scenario.value,
                    date_label=_time.strftime("%B %Y"),
                    crisis=sc.crisis_title,
                    decision=(
                        f"Hybrid route — ${logistics['cost_usd'] // 1000}K / "
                        f"{logistics.get('transit_hours', 36)}h"
                    ),
                    outcome=(
                        f"Resolved in {elapsed(started_at)}. "
                        f"MC confidence {int(mc_res.get('confidence_interval', 0.94) * 100)}%."
                    ),
                    cost_usd=logistics["cost_usd"],
                    saved_usd=max(saved, 0),
                    key_learning=(
                        "Hybrid beat air-only by ~"
                        f"${finance.get('customs_surcharge', 0) // 1000}K customs surcharge."
                    ),
                    confidence=mc_res.get("confidence_interval", 0.94),
                )
    except Exception as mem_exc:
        print(f"   [orchestrator.graph] TursoDB persist skipped: {mem_exc}")

    state["run_context"] = run_context
    return state


def _build_orchestrator_graph() -> Any:
    """Construct and compile the orchestrator StateGraph."""
    graph = StateGraph(RunGraphState)

    graph.add_node("phase0_broadcast", _phase0_broadcast)
    graph.add_node("round1_parallel", _round1_parallel)
    graph.add_node("round2_finance", _round2_finance)
    graph.add_node("round2b_logistics_revise", _round2b_logistics_revise)
    graph.add_node("round3_sales", _round3_sales)
    graph.add_node("round4_risk", _round4_risk)
    graph.add_node(
        "round5_finance_and_procurement_ack",
        _round5_finance_and_procurement_ack,
    )
    graph.add_node("awaiting_approval", _awaiting_approval)

    graph.set_entry_point("phase0_broadcast")
    graph.add_edge("phase0_broadcast", "round1_parallel")
    graph.add_edge("round1_parallel", "round2_finance")
    graph.add_edge("round2_finance", "round2b_logistics_revise")
    graph.add_edge("round2b_logistics_revise", "round3_sales")
    graph.add_edge("round3_sales", "round4_risk")
    graph.add_edge("round4_risk", "round5_finance_and_procurement_ack")
    graph.add_edge("round5_finance_and_procurement_ack", "awaiting_approval")

    compiled = graph.compile()
    return compiled


_GRAPH_APP = _build_orchestrator_graph()


async def run_scenario_graph(
    run_id: str,
    scenario: ScenarioType,
) -> RunGraphState:
    """
    Public entry point for running a scenario via LangGraph.

    Orchestrator.run_scenario() delegates here when USE_LIVE_AGENTS is true.
    """
    initial_state: RunGraphState = {
        "run_id": run_id,
        "scenario": scenario,
        "status": RunStatus.PENDING,
        "run_context": {},
        "started_at": time.time(),
    }
    final_state: RunGraphState = await _GRAPH_APP.ainvoke(initial_state)
    return final_state


__all__ = ["run_scenario_graph", "RunGraphState"]


