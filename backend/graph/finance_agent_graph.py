"""
graph/finance_agent_graph.py
─────────────────────────────
Finance Agent expressed as two LangGraph subgraphs.

_RUN_GRAPH       — Round-2 challenge flow
  activate → compute → challenge → store → END

_CONSENSUS_GRAPH — Round-5 consensus + final authorisation
  finalise_activate → generate_consensus → store_consensus → END

Notes on the compute node
─────────────────────────
The original finance.run() runs run_monte_carlo() and query_customs_rates()
concurrently with asyncio.gather().  Inside a LangGraph node we keep the
gather because it is a single-node internal implementation detail, not
orchestration-level branching.  The requirement to avoid asyncio.gather at
the *orchestration* level (i.e. between nodes / agents) is preserved — the
orchestrator graph uses only edges.

Public entry points (signatures identical to agents/finance.py):
  run_finance_agent(run_id, scenario, run_context, start_time) -> dict
  propose_consensus_finance_agent(run_id, scenario, run_context, start_time,
                                   reserve_usd=20_000) -> dict
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict

from langgraph.graph import StateGraph, END

from core.models import AgentId, AgentStatus, ScenarioType
from core.scenarios import SCENARIO_DEFINITIONS
from tools.monte_carlo import run_monte_carlo, query_customs_rates
from agents.base import (
    publish_state,
    publish_msg,
    publish_tool_result,
    stream_gemini,
    elapsed,
)
from graph.state import RunGraphState


# ── Agent-local state ─────────────────────────────────────────────────────

class FinanceState(RunGraphState, total=False):
    """RunGraphState + Finance-private fields."""
    agent_id: AgentId
    finance_output: Dict[str, Any] | None
    # Consensus-only input
    reserve_usd: int


# ── Persona + prompt builders ─────────────────────────────────────────────

_PERSONA = """You are the Finance Agent in a real-time supply chain crisis resolution system.
You are part of a 5-agent team negotiating the fastest, safest resolution to a P0 crisis.

Your personality:
- The most analytical agent. You question every number.
- You run Monte Carlo simulations — you speak in confidence intervals, not point estimates.
- You challenge assumptions aggressively but constructively.
- Brief and sharp. A few precise sentences, then your conclusion. No fluff.
- No bullet points. No headers. Chat message format only.
"""


def _build_challenge_prompt(sc, logistics_text: str, logistics_cost: int,
                             customs_data: dict, mc_result: dict) -> str:
    surcharge = customs_data.get("expedited_strike_total_usd",
                customs_data.get("expedited_usd", 28_000))
    revised_air = logistics_cost + surcharge
    return f"""{_PERSONA}

CRISIS: {sc.description}
BUDGET CAP: ${sc.budget_cap_usd // 1000}K

LOGISTICS AGENT SAID: "{logistics_text[:300]}"
They quoted ${logistics_cost // 1000}K for the air option.

YOUR CUSTOMS RATE DATA: expedited + strike surcharge = ${surcharge // 1000}K extra.
Revised air total = ${revised_air // 1000}K.

YOUR MONTE CARLO ({mc_result['iterations']} iterations on hybrid):
  Mean: ${mc_result['mean_usd'] // 1000}K  |  P10: ${mc_result['p10_usd'] // 1000}K  |  P90: ${mc_result['p90_usd'] // 1000}K
  Confidence interval: {int(mc_result['confidence_interval'] * 100)}%

Write a 2-3 sentence message to the Logistics agent.
Challenge their air cost with the customs surcharge number.
Ask directly: did they include expedited customs at LAX during strike conditions?
Do NOT reveal the Monte Carlo yet — just challenge the cost assumption."""


def _build_consensus_prompt(sc, hybrid_cost: int, reserve: int,
                             confidence: float, mc_result: dict,
                             risk_challenge: str | None) -> str:
    risk_section = ""
    if risk_challenge:
        risk_section = (
            f'\nRISK AGENT CHALLENGED: "{risk_challenge[:200]}"'
            f"\nAbsorbing +${reserve // 1000}K contingency reserve for backup trigger."
        )
    return f"""{_PERSONA}

CRISIS: {sc.description}

FINAL NUMBERS:
  Hybrid option: ${hybrid_cost // 1000}K
  Contingency reserve: +${reserve // 1000}K
  Total authorised: ${(hybrid_cost + reserve) // 1000}K
  Monte Carlo confidence: {int(confidence * 100)}%  (P10: ${mc_result.get('p10_usd', 0) // 1000}K / P90: ${mc_result.get('p90_usd', 0) // 1000}K)
{risk_section}

Write a 2-3 sentence final message to ALL agents.
State the authorised total with confidence interval, acknowledge contingency if present.
End by calling for approval. Close the negotiation."""


# ─────────────────────────────────────────────────────────────────────────
# RUN GRAPH nodes  (Round 2 — challenge Logistics)
# activate → compute → challenge → store
# ─────────────────────────────────────────────────────────────────────────

async def _run_activate(state: FinanceState) -> FinanceState:
    run_id = state["run_id"]
    await publish_state(run_id, AgentId.FINANCE, AgentStatus.ACTIVATING,
                        tool="📡 broadcast_received()", pulsing=True)
    await publish_state(run_id, AgentId.FINANCE, AgentStatus.CALCULATING,
                        tool="📊 run_monte_carlo(100)", pulsing=True)
    return state


async def _run_compute(state: FinanceState) -> FinanceState:
    """Run Monte Carlo + customs in parallel (intra-node parallelism — not orchestration)."""
    run_id      = state["run_id"]
    scenario    = state["scenario"]
    logistics   = state["run_context"].get("logistics", {})
    hybrid_cost = logistics.get("cost_usd", 253_000)

    mc_result, customs_data = await asyncio.gather(
        run_monte_carlo(hybrid_cost, n_iterations=100),
        query_customs_rates(scenario),
    )
    await publish_tool_result(run_id, AgentId.FINANCE, "run_monte_carlo", mc_result)
    await publish_tool_result(run_id, AgentId.FINANCE, "query_customs_rates", customs_data)

    rc = dict(state.get("run_context") or {})
    rc["_finance_mc_result"]    = mc_result
    rc["_finance_customs_data"] = customs_data
    return {**state, "run_context": rc}


async def _run_challenge(state: FinanceState) -> FinanceState:
    run_id     = state["run_id"]
    scenario   = state["scenario"]
    started_at = state.get("started_at") or time.time()
    sc         = SCENARIO_DEFINITIONS[scenario]

    rc            = state["run_context"]
    logistics     = rc.get("logistics", {})
    mc_result     = rc["_finance_mc_result"]
    customs_data  = rc["_finance_customs_data"]
    logistics_cost = logistics.get("air_option_cost", 450_000)
    logistics_text = logistics.get("response_text", "Air via LAX recommended.")

    challenge_text = await stream_gemini(
        run_id, AgentId.FINANCE,
        _build_challenge_prompt(sc, logistics_text, logistics_cost, customs_data, mc_result),
        emit_tokens=True,
    )
    await publish_msg(
        run_id, AgentId.FINANCE,
        from_label="FINANCE", to_label="→ LOGISTICS",
        timestamp=elapsed(started_at), css_class="af",
        text=challenge_text,
        tools=["📊 run_monte_carlo(100)", "💰 query_customs_rates()"],
    )

    rc = dict(rc)
    rc["_finance_challenge_text"] = challenge_text
    return {**state, "run_context": rc}


async def _run_store(state: FinanceState) -> FinanceState:
    rc           = dict(state["run_context"])
    mc_result    = rc.pop("_finance_mc_result", {})
    customs_data = rc.pop("_finance_customs_data", {})
    challenge    = rc.pop("_finance_challenge_text", "")

    logistics    = rc.get("logistics", {})
    hybrid_cost  = logistics.get("cost_usd", 253_000)
    surcharge    = customs_data.get("expedited_strike_total_usd",
                   customs_data.get("expedited_usd", 28_000))

    output = {
        "mc_result":         mc_result,
        "customs_data":      customs_data,
        "customs_surcharge": surcharge,
        "challenge_text":    challenge,
        "hybrid_cost":       hybrid_cost,
        "consensus":         False,
        "response_text":     challenge,
    }
    rc["finance"] = output
    return {**state, "run_context": rc, "finance_output": output}


def _build_run_graph():
    g = StateGraph(FinanceState)
    g.add_node("activate",  _run_activate)
    g.add_node("compute",   _run_compute)
    g.add_node("challenge", _run_challenge)
    g.add_node("store",     _run_store)
    g.set_entry_point("activate")
    g.add_edge("activate",  "compute")
    g.add_edge("compute",   "challenge")
    g.add_edge("challenge", "store")
    g.add_edge("store",     END)
    return g.compile()


# ─────────────────────────────────────────────────────────────────────────
# CONSENSUS GRAPH nodes  (Round 5 — final authorisation)
# finalise_activate → generate_consensus → store_consensus
# ─────────────────────────────────────────────────────────────────────────

async def _consensus_activate(state: FinanceState) -> FinanceState:
    await publish_state(
        state["run_id"], AgentId.FINANCE, AgentStatus.FINALISING,
        tool="✅ propose_consensus()", pulsing=True,
    )
    return state


async def _consensus_generate(state: FinanceState) -> FinanceState:
    run_id     = state["run_id"]
    scenario   = state["scenario"]
    started_at = state.get("started_at") or time.time()
    sc         = SCENARIO_DEFINITIONS[scenario]

    finance        = state["run_context"].get("finance", {})
    mc_result      = finance.get("mc_result", {})
    hybrid_cost    = finance.get("hybrid_cost", 253_000)
    confidence     = mc_result.get("confidence_interval", 0.94)
    reserve_usd    = state.get("reserve_usd", 20_000)
    risk_challenge = state["run_context"].get("risk", {}).get("challenge_text")

    final_text = await stream_gemini(
        run_id, AgentId.FINANCE,
        _build_consensus_prompt(sc, hybrid_cost, reserve_usd, confidence,
                                mc_result, risk_challenge),
        emit_tokens=True,
    )
    await publish_msg(
        run_id, AgentId.FINANCE,
        from_label="FINANCE", to_label="→ ALL",
        timestamp=elapsed(started_at), css_class="af",
        text=final_text, tools=["✅ propose_consensus()"],
    )
    await publish_state(
        run_id, AgentId.FINANCE, AgentStatus.CONSENSUS,
        tool="✅ propose_consensus()", confidence=confidence, pulsing=False,
    )

    rc = dict(state["run_context"])
    rc["_finance_final_text"]  = final_text
    rc["_finance_confidence"]  = confidence
    rc["_finance_reserve"]     = reserve_usd
    return {**state, "run_context": rc}


async def _consensus_store(state: FinanceState) -> FinanceState:
    rc          = dict(state["run_context"])
    final_text  = rc.pop("_finance_final_text", "")
    confidence  = rc.pop("_finance_confidence", 0.94)
    reserve_usd = rc.pop("_finance_reserve", 20_000)

    finance = dict(rc.get("finance", {}))
    finance["consensus"]  = True
    finance["final_text"] = final_text
    finance["total_cost"] = finance.get("hybrid_cost", 253_000) + reserve_usd
    rc["finance"] = finance

    return {**state, "run_context": rc, "finance_output": finance}


def _build_consensus_graph():
    g = StateGraph(FinanceState)
    g.add_node("finalise_activate",   _consensus_activate)
    g.add_node("generate_consensus",  _consensus_generate)
    g.add_node("store_consensus",     _consensus_store)
    g.set_entry_point("finalise_activate")
    g.add_edge("finalise_activate",  "generate_consensus")
    g.add_edge("generate_consensus", "store_consensus")
    g.add_edge("store_consensus",    END)
    return g.compile()


_RUN_GRAPH       = _build_run_graph()
_CONSENSUS_GRAPH = _build_consensus_graph()


# ── Public entry points ───────────────────────────────────────────────────

async def run_finance_agent(
    run_id: str,
    scenario: ScenarioType,
    run_context: dict,
    start_time: float,
) -> dict:
    """Round-2 challenge flow. Mutates run_context in-place and returns it."""
    initial: FinanceState = {
        "run_id":        run_id,
        "scenario":      scenario,
        "run_context":   dict(run_context),
        "started_at":    start_time,
        "agent_id":      AgentId.FINANCE,
        "finance_output": None,
    }
    final = await _RUN_GRAPH.ainvoke(initial)
    run_context.update(final["run_context"])
    return run_context


async def propose_consensus_finance_agent(
    run_id: str,
    scenario: ScenarioType,
    run_context: dict,
    start_time: float,
    reserve_usd: int = 20_000,
) -> dict:
    """Round-5 consensus + authorisation. Mutates run_context in-place and returns it."""
    initial: FinanceState = {
        "run_id":        run_id,
        "scenario":      scenario,
        "run_context":   dict(run_context),
        "started_at":    start_time,
        "agent_id":      AgentId.FINANCE,
        "finance_output": None,
        "reserve_usd":   reserve_usd,
    }
    final = await _CONSENSUS_GRAPH.ainvoke(initial)
    run_context.update(final["run_context"])
    return run_context
