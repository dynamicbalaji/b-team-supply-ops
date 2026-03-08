"""
graph/orchestrator_graph.py
───────────────────────────
Two compiled LangGraph graphs that drive the entire live scenario lifecycle.
All business-logic control flow is expressed as graph edges; there is no
hand-written asyncio orchestration in this file or its callers.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Graph 1: _SCENARIO_GRAPH  (pre-approval)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  phase0_broadcast
    └─► round1_logistics
          └─► round1_procurement
                └─► round2_finance
                      └─► round2b_logistics_revise
                            └─► round3_sales
                                  └─► round4_risk
                                        └─► round5_consensus
                                              └─► awaiting_approval → END

Entry point: run_scenario_graph(run_id, scenario)
Called by:   orchestrator.run_scenario()  (background task from POST /api/runs)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Graph 2: _CASCADE_GRAPH  (post-approval execution)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  exec_phase_transition
    └─► exec_logistics_confirm
          └─► exec_sales_notify
                └─► exec_finance_release
                      └─► exec_procurement_cancel
                            └─► exec_complete → END

Entry point: run_execution_cascade_graph(run_id)
Called by:   orchestrator.run_execution_cascade()  (background task from POST /approve)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
asyncio discipline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
No asyncio.gather / asyncio.sleep / asyncio.create_task appears at the
orchestration level in this file.  The only concurrency primitive used is
`await graph.ainvoke(state)` — LangGraph drives the execution schedule.

Intra-node parallelism (e.g. Finance fetching Monte Carlo + customs rates
simultaneously inside a single node via asyncio.gather) is permitted because
it is scoped to the computation of a single logical step, not cross-agent
control flow.

Event emission: every SSE event (TokenEvent, AgentStateEvent, ToolResultEvent,
MessageEvent, …) is published directly to Redis inside the node that produces
it, using redis_client.publish().  The SSE endpoint (sse.py) polls Redis
independently — it has no knowledge of LangGraph and needs no changes.
"""

from __future__ import annotations

import time
from typing import Any, TypedDict

from langgraph.graph import StateGraph, END

import redis_client
from models import (
    AgentId,
    AgentStatus,
    RunStatus,
    ScenarioType,
    ApprovalRequiredEvent,
)
from orchestrator import set_run_status
from scenarios import SCENARIO_DEFINITIONS
from agents.base import elapsed, publish_state

# Agent subgraph entry points — imported directly, bypassing shim layer
from graph.logistics_agent_graph import run_logistics_agent, revise_logistics_agent
from graph.finance_agent_graph import run_finance_agent, propose_consensus_finance_agent
from graph.procurement_agent_graph import run_procurement_agent
from graph.sales_agent_graph import run_sales_agent
from graph.risk_agent_graph import run_risk_agent

from agents.orchestrator_live import _orc_msg, _phase, _map, _safe_context_summary
from .state import RunGraphState


# ─────────────────────────────────────────────────────────────────────────
# Orchestration nodes
# ─────────────────────────────────────────────────────────────────────────

async def _phase0_broadcast(state: RunGraphState) -> RunGraphState:
    """Phase 0→1: Orchestrator broadcasts the crisis and activates agents."""
    run_id     = state["run_id"]
    scenario   = state["scenario"]
    started_at = state.get("started_at") or time.time()

    sc = SCENARIO_DEFINITIONS[scenario]

    await _phase(run_id, 0, "done")
    await _phase(run_id, 1, "active")
    from scenarios import _orchestrator_broadcast
    await _orc_msg(
        run_id,
        _orchestrator_broadcast(sc),
        elapsed(started_at),
    )
    await _map(run_id, "AGENTS ACTIVE", "#ffb340", "Evaluating routes")

    set_run_status(run_id, RunStatus.RUNNING)
    run_context = dict(state.get("run_context") or {})
    return {**state, "started_at": started_at, "status": RunStatus.RUNNING,
            "run_context": run_context}


async def _round1_logistics(state: RunGraphState) -> RunGraphState:
    """Round 1a: Logistics main run."""
    run_context = dict(state["run_context"])
    await run_logistics_agent(
        state["run_id"], state["scenario"], run_context, state["started_at"]
    )
    return {**state, "run_context": run_context}


async def _round1_procurement(state: RunGraphState) -> RunGraphState:
    """Round 1b: Procurement main run (sequential after Logistics)."""
    run_context = dict(state["run_context"])
    await run_procurement_agent(
        state["run_id"], state["scenario"], run_context, state["started_at"]
    )
    await _phase(state["run_id"], 1, "done")
    await _phase(state["run_id"], 2, "active")
    return {**state, "run_context": run_context}


async def _round2_finance(state: RunGraphState) -> RunGraphState:
    """Round 2: Finance challenges Logistics."""
    run_context = dict(state["run_context"])
    await run_finance_agent(
        state["run_id"], state["scenario"], run_context, state["started_at"]
    )
    return {**state, "run_context": run_context}


async def _round2b_logistics_revise(state: RunGraphState) -> RunGraphState:
    """Round 2b: Logistics absorbs Finance challenge and pivots to hybrid."""
    run_context       = dict(state["run_context"])
    finance_out       = run_context.get("finance", {})
    customs_surcharge = finance_out.get("customs_surcharge", 50_000)
    challenge_text    = finance_out.get("challenge_text", "Customs surcharge applies.")

    await revise_logistics_agent(
        state["run_id"], state["scenario"], run_context, state["started_at"],
        challenge=challenge_text,
        customs_surcharge=customs_surcharge,
    )
    return {**state, "run_context": run_context}


async def _round3_sales(state: RunGraphState) -> RunGraphState:
    """Round 3: Sales negotiates SLA amendment."""
    run_context = dict(state["run_context"])
    await run_sales_agent(
        state["run_id"], state["scenario"], run_context, state["started_at"]
    )
    return {**state, "run_context": run_context}


async def _round4_risk(state: RunGraphState) -> RunGraphState:
    """Round 4: Risk Agent fires Devil's Advocate challenge."""
    run_context = dict(state["run_context"])
    await run_risk_agent(
        state["run_id"], state["scenario"], run_context, state["started_at"]
    )
    return {**state, "run_context": run_context}


async def _round5_consensus(state: RunGraphState) -> RunGraphState:
    """
    Round 5: Finance proposes final consensus; Procurement acknowledges.

    Procurement acknowledge is publish_state only — not a full subgraph run.
    """
    run_id      = state["run_id"]
    scenario    = state["scenario"]
    started_at  = state["started_at"]
    run_context = dict(state["run_context"])

    await propose_consensus_finance_agent(
        run_id, scenario, run_context, started_at, reserve_usd=20_000
    )

    # Procurement acknowledgement (matches original agents/procurement.acknowledge())
    await publish_state(
        run_id, AgentId.PROCUREMENT, AgentStatus.DONE,
        tool="✅ acknowledged()", confidence=0.71, pulsing=False,
    )
    run_context.setdefault("procurement", {})["consensus"] = True

    return {**state, "run_context": run_context}


async def _awaiting_approval(state: RunGraphState) -> RunGraphState:
    """
    Final node: emit ApprovalRequiredEvent, persist to TursoDB, set status.
    No agent logic — pure orchestration.
    """
    run_id      = state["run_id"]
    scenario    = state["scenario"]
    started_at  = state["started_at"]
    run_context = dict(state["run_context"])
    sc          = SCENARIO_DEFINITIONS[scenario]

    await _phase(run_id, 2, "done")
    await _phase(run_id, 3, "active")

    finance_final = run_context.get("finance", {})
    mc            = finance_final.get("mc_result", {})
    hybrid_cost   = finance_final.get("hybrid_cost", 253_000)
    confidence    = mc.get("confidence_interval", 0.94)
    transit_hours = run_context.get("logistics", {}).get("transit_hours", 36)

    await redis_client.publish(
        run_id,
        ApprovalRequiredEvent(
            option="hybrid",
            label="Hybrid Route — 60% Air / 40% Sea",
            cost_usd=hybrid_cost,
            reserve_usd=20_000,
            delivery_hours=transit_hours,
            confidence=confidence,
            detail=(
                f"${hybrid_cost // 1000}K + $20K reserve · "
                f"{transit_hours}h delivery · "
                f"Backup trigger H20 · {sc.customer}: ✓ · "
                f"Confidence: {int(confidence * 100)}%"
            ),
        ).model_dump(),
    )
    await _map(run_id, "AWAITING APPROVAL", "#ffb340")

    set_run_status(run_id, RunStatus.AWAITING_APPROVAL)

    safe_ctx = _safe_context_summary(run_context)
    await redis_client.set_run_state(
        run_id,
        {
            "run_id":   run_id,
            "scenario": scenario,
            "status":   RunStatus.AWAITING_APPROVAL,
            "context":  safe_ctx,
        },
    )

    # Persist run context + episodic memory to TursoDB (best-effort)
    try:
        import turso_client
        if turso_client.is_configured():
            await turso_client.save_run_context(run_id, run_context)

            logistics = run_context.get("logistics", {})
            finance   = run_context.get("finance", {})
            if logistics.get("cost_usd") and finance.get("mc_result"):
                import time as _time
                mc_res = finance["mc_result"]
                saved  = sc.penalty_usd - logistics.get("cost_usd", 0)
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

    return {**state, "run_context": run_context, "status": RunStatus.AWAITING_APPROVAL}


# ── Graph assembly ────────────────────────────────────────────────────────

def _build_orchestrator_graph() -> Any:
    g = StateGraph(RunGraphState)

    g.add_node("phase0_broadcast",         _phase0_broadcast)
    g.add_node("round1_logistics",         _round1_logistics)
    g.add_node("round1_procurement",       _round1_procurement)
    g.add_node("round2_finance",           _round2_finance)
    g.add_node("round2b_logistics_revise", _round2b_logistics_revise)
    g.add_node("round3_sales",             _round3_sales)
    g.add_node("round4_risk",              _round4_risk)
    g.add_node("round5_consensus",         _round5_consensus)
    g.add_node("awaiting_approval",        _awaiting_approval)

    g.set_entry_point("phase0_broadcast")
    g.add_edge("phase0_broadcast",         "round1_logistics")
    g.add_edge("round1_logistics",         "round1_procurement")
    g.add_edge("round1_procurement",       "round2_finance")
    g.add_edge("round2_finance",           "round2b_logistics_revise")
    g.add_edge("round2b_logistics_revise", "round3_sales")
    g.add_edge("round3_sales",             "round4_risk")
    g.add_edge("round4_risk",              "round5_consensus")
    g.add_edge("round5_consensus",         "awaiting_approval")
    g.add_edge("awaiting_approval",        END)

    return g.compile()


_GRAPH_APP = _build_orchestrator_graph()


# ─────────────────────────────────────────────────────────────────────────
# Graph 2: Post-approval execution cascade
# ─────────────────────────────────────────────────────────────────────────
# Replaces the manual asyncio.sleep timing loop in orchestrator.run_execution_cascade.
# Each node publishes one execution-phase event directly to Redis.
# The cascade state only needs run_id — no agent business logic here.
# ─────────────────────────────────────────────────────────────────────────



class _CascadeState(TypedDict, total=False):
    run_id:     str
    started_at: float
    scenario:   ScenarioType


async def _exec_phase_transition(state: _CascadeState) -> _CascadeState:
    """Mark phase 3 done → phase 4 active; update map to EXECUTING."""
    run_id = state["run_id"]
    await _phase(run_id, 3, "done")
    await _phase(run_id, 4, "active")
    await _map(run_id, "EXECUTING", "#00e676", "✈ Freight booked → Austin TX")
    return state


async def _exec_logistics_confirm(state: _CascadeState) -> _CascadeState:
    """Logistics: freight booking confirmation."""
    from models import ExecutionEvent, AgentStatus, AgentId, AgentStateEvent
    from agents.base import elapsed as _elapsed

    run_id     = state["run_id"]
    started_at = state.get("started_at") or time.time()

    from scenarios import _logistics_exec_message, SCENARIO_DEFINITIONS
    scenario = state.get("scenario", ScenarioType.PORT_STRIKE)
    sc = SCENARIO_DEFINITIONS[scenario]
    await redis_client.publish(run_id, ExecutionEvent(
        agent=AgentId.LOGISTICS,
        from_label="✈ LOGISTICS",
        css_class="al",
        timestamp=_elapsed(started_at),
        text=_logistics_exec_message(sc),
    ).model_dump())
    await publish_state(run_id, AgentId.LOGISTICS, AgentStatus.COMPLETE,
                        tool="✅ done", confidence=0.88, pulsing=False)
    return state


async def _exec_sales_notify(state: _CascadeState) -> _CascadeState:
    """Sales: customer notification confirmation."""
    from models import ExecutionEvent, AgentStatus, AgentId
    from agents.base import elapsed as _elapsed

    run_id     = state["run_id"]
    started_at = state.get("started_at") or time.time()

    from scenarios import _sales_exec_message, SCENARIO_DEFINITIONS
    scenario = state.get("scenario", ScenarioType.PORT_STRIKE)
    sc = SCENARIO_DEFINITIONS[scenario]
    await redis_client.publish(run_id, ExecutionEvent(
        agent=AgentId.SALES,
        from_label="📧 SALES",
        css_class="as_",
        timestamp=_elapsed(started_at),
        text=_sales_exec_message(sc),
    ).model_dump())
    await publish_state(run_id, AgentId.SALES, AgentStatus.COMPLETE,
                        tool="✅ done", confidence=0.97, pulsing=False)
    return state


async def _exec_finance_release(state: _CascadeState) -> _CascadeState:
    """Finance: budget release confirmation."""
    from models import ExecutionEvent, AgentStatus, AgentId
    from agents.base import elapsed as _elapsed

    run_id     = state["run_id"]
    started_at = state.get("started_at") or time.time()

    from scenarios import _finance_exec_message, SCENARIO_DEFINITIONS
    scenario = state.get("scenario", ScenarioType.PORT_STRIKE)
    sc = SCENARIO_DEFINITIONS[scenario]
    cost = state.get("run_context", {}).get("finance", {}).get("hybrid_cost", 280_000) if state.get("run_context") else 280_000
    await redis_client.publish(run_id, ExecutionEvent(
        agent=AgentId.FINANCE,
        from_label="💰 FINANCE",
        css_class="af",
        timestamp=_elapsed(started_at),
        text=_finance_exec_message(sc, cost),
    ).model_dump())
    await publish_state(run_id, AgentId.FINANCE, AgentStatus.COMPLETE,
                        tool="✅ done", confidence=0.94, pulsing=False)
    return state


async def _exec_procurement_cancel(state: _CascadeState) -> _CascadeState:
    """Procurement: cancel spot order, schedule Tucson backup."""
    from models import ExecutionEvent, AgentStatus, AgentId
    from agents.base import elapsed as _elapsed

    run_id     = state["run_id"]
    started_at = state.get("started_at") or time.time()

    from scenarios import _procurement_last_message, SCENARIO_DEFINITIONS
    scenario = state.get("scenario", ScenarioType.PORT_STRIKE)
    sc = SCENARIO_DEFINITIONS[scenario]
    await redis_client.publish(run_id, ExecutionEvent(
        agent=AgentId.PROCUREMENT,
        from_label="🚫 PROCUREMENT",
        css_class="ap",
        timestamp=_elapsed(started_at),
        text=_procurement_last_message(sc),
    ).model_dump())
    await publish_state(run_id, AgentId.PROCUREMENT, AgentStatus.COMPLETE,
                        tool="✅ done", confidence=0.71, pulsing=False)
    return state


async def _exec_complete(state: _CascadeState) -> _CascadeState:
    """Final cascade node: phase 4 done → DELIVERED map → CompleteEvent."""
    from models import CompleteEvent
    from agents.base import elapsed as _elapsed

    run_id     = state["run_id"]
    started_at = state.get("started_at") or time.time()

    await _phase(run_id, 4, "done")
    await _phase(run_id, 5, "active")
    await _map(run_id, "DELIVERED ✅", "#00e676")
    await redis_client.publish(run_id, CompleteEvent(
        resolution_time=_elapsed(started_at),
        cost_usd=280_000,
        saved_usd=220_000,
        message_count=9,
    ).model_dump())
    await _phase(run_id, 5, "done")
    return state


def _build_cascade_graph():
    g = StateGraph(_CascadeState)

    g.add_node("exec_phase_transition",  _exec_phase_transition)
    g.add_node("exec_logistics_confirm", _exec_logistics_confirm)
    g.add_node("exec_sales_notify",      _exec_sales_notify)
    g.add_node("exec_finance_release",   _exec_finance_release)
    g.add_node("exec_procurement_cancel",_exec_procurement_cancel)
    g.add_node("exec_complete",          _exec_complete)

    g.set_entry_point("exec_phase_transition")
    g.add_edge("exec_phase_transition",  "exec_logistics_confirm")
    g.add_edge("exec_logistics_confirm", "exec_sales_notify")
    g.add_edge("exec_sales_notify",      "exec_finance_release")
    g.add_edge("exec_finance_release",   "exec_procurement_cancel")
    g.add_edge("exec_procurement_cancel","exec_complete")
    g.add_edge("exec_complete",          END)

    return g.compile()


_CASCADE_GRAPH = _build_cascade_graph()


# ── Public entry points ────────────────────────────────────────────────────

async def run_scenario_graph(
    run_id: str,
    scenario: ScenarioType,
) -> RunGraphState:
    """
    Entry point for the pre-approval scenario graph.
    Called by orchestrator.run_scenario() when USE_LIVE_AGENTS is True.

    The single `await _GRAPH_APP.ainvoke(state)` call is the only
    concurrency primitive at the orchestration level — LangGraph drives
    the node-by-node execution schedule.  Every SSE event is published
    to Redis inside the node that produces it; sse.py polls Redis
    independently with no knowledge of this graph.
    """
    initial_state: RunGraphState = {
        "run_id":      run_id,
        "scenario":    scenario,
        "status":      RunStatus.PENDING,
        "run_context": {},
        "started_at":  time.time(),
    }
    final_state: RunGraphState = await _GRAPH_APP.ainvoke(initial_state)
    return final_state


async def run_execution_cascade_graph(run_id: str, started_at: float) -> None:
    """
    Entry point for the post-approval execution cascade graph.
    Called by orchestrator.run_execution_cascade() when USE_LIVE_AGENTS is True.

    Publishes execution-phase events (freight confirmed, customer notified,
    budget released, etc.) and the final CompleteEvent — all via direct
    Redis publish inside each node.  No asyncio.sleep timing loops here;
    the node sequence itself is the execution schedule.
    """
    # Load scenario from Redis state so cascade messages are scenario-aware
    try:
        run_state = await redis_client.get_run_state(run_id)
        scenario_val = (run_state or {}).get("scenario", ScenarioType.PORT_STRIKE)
        if isinstance(scenario_val, str):
            scenario_val = ScenarioType(scenario_val)
    except Exception:
        scenario_val = ScenarioType.PORT_STRIKE

    initial: _CascadeState = {
        "run_id":     run_id,
        "started_at": started_at,
        "scenario":   scenario_val,
    }
    await _CASCADE_GRAPH.ainvoke(initial)


__all__ = ["run_scenario_graph", "run_execution_cascade_graph", "RunGraphState"]
