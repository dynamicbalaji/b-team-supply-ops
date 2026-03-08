"""
graph/logistics_agent_graph.py
───────────────────────────────
Logistics Agent expressed as two LangGraph subgraphs.

_RUN_GRAPH   — Round-1 main flow
  activate → fetch_rates → recall_memory → generate → store → END

_REVISE_GRAPH — Round-2b Finance-challenge absorption
  revise_activate → generate_revision → store_revision → END

Both graphs share the same LogisticsState TypedDict.
Each is compiled once at import time (stateless; safe for concurrent runs).

Public entry points (signatures identical to agents/logistics.py):
  run_logistics_agent(run_id, scenario, run_context, start_time) -> dict
  revise_logistics_agent(run_id, scenario, run_context, start_time,
                          challenge, customs_surcharge) -> dict
"""

from __future__ import annotations

import time
from typing import Any, Dict

from langgraph.graph import StateGraph, END

from core.models import AgentId, AgentStatus, ScenarioType
from core.scenarios import SCENARIO_DEFINITIONS
from tools.freight import check_freight_rates, memory_recall, recalculate_route
from agents.base import (
    publish_state,
    publish_msg,
    publish_tool_result,
    stream_gemini,
    elapsed,
)
from graph.state import RunGraphState


# ── Agent-local state ─────────────────────────────────────────────────────

class LogisticsState(RunGraphState, total=False):
    """RunGraphState + Logistics-private fields."""
    agent_id: AgentId
    logistics_output: Dict[str, Any] | None
    # Revise-only inputs (populated before _REVISE_GRAPH.ainvoke)
    challenge: str
    customs_surcharge: int


# ── Persona + prompt builders ─────────────────────────────────────────────

_PERSONA = """You are the Logistics Agent in a real-time supply chain crisis resolution system.
You are part of a 5-agent team negotiating the fastest, safest resolution to a P0 crisis.

Your personality:
- Direct and numerical. Always cite specific dollar amounts, hours, and percentages.
- You recall historical precedents from memory — you've seen similar crises before.
- You propose solutions with clear tradeoffs, never just one option.
- You speak in short, punchy sentences like a seasoned ops manager under pressure.
- You are addressing the orchestrator and your fellow agents, not a human customer.

Output format:
- 3-4 sentences maximum
- Lead with your top recommendation
- Include cost, hours, risk level
- Reference memory if relevant (cite the date and savings)
- End with a note about what you're uncertain about
- NO bullet points, NO headers, NO markdown formatting
- Write as a live message in a negotiation chat
"""


def _build_run_prompt(sc, rates: dict, memory: dict | None) -> str:
    rates_summary = "\n".join(
        f"  {k}: ${v.get('cost_usd', 0) // 1000}K / {v.get('transit_hours')}h"
        f" / {v.get('risk_level')} risk — {v.get('carrier', '')}"
        for k, v in rates.items()
    )
    memory_section = ""
    if memory:
        memory_section = (
            f"\nEpisodic memory match ({memory.get('date', '?')}): "
            f"{memory.get('crisis', '')}. "
            f"We chose: {memory.get('decision', '')}. "
            f"Saved ${memory.get('saved_usd', 0) // 1000}K. "
            f"Confidence: {int(memory.get('confidence', 0) * 100)}%."
        )
    return f"""{_PERSONA}

CRISIS: {sc.description}
CUSTOMER: {sc.customer}
BUDGET CAP: ${sc.budget_cap_usd // 1000}K
DEADLINE: {sc.deadline_hours}h
{memory_section}

FREIGHT OPTIONS (live from check_freight_rates()):
{rates_summary}

Write your message to the Orchestrator now. Recommend one primary option and mention the hybrid as backup.
Reference the memory date and savings if you recalled one. Flag your biggest single uncertainty."""


def _build_revise_prompt(sc, logistics_out: dict, air_cost: int,
                          customs_surcharge: int, challenge: str) -> str:
    revised_air = air_cost + customs_surcharge
    return f"""{_PERSONA}

Finance challenged your ${air_cost // 1000}K air estimate: "{challenge}"
recalculate_route() confirms: air total = ${revised_air // 1000}K — at/over budget cap of ${sc.budget_cap_usd // 1000}K.
The hybrid 60/40 option at ${logistics_out.get('cost_usd', 253_000) // 1000}K / {logistics_out.get('transit_hours', 36)}h is now clearly better.

Write a 2-sentence acknowledgment: confirm finance is correct with the revised air total, then pivot your recommendation to hybrid.
No headers, no bullets, speak as yourself in the chat."""


# ─────────────────────────────────────────────────────────────────────────
# RUN GRAPH nodes
# ─────────────────────────────────────────────────────────────────────────

async def _run_activate(state: LogisticsState) -> LogisticsState:
    await publish_state(
        state["run_id"], AgentId.LOGISTICS, AgentStatus.ACTIVATING,
        tool="📡 broadcast_received()", pulsing=True,
    )
    return state


async def _run_fetch_rates(state: LogisticsState) -> LogisticsState:
    run_id = state["run_id"]
    await publish_state(run_id, AgentId.LOGISTICS, AgentStatus.PROPOSING,
                        tool="📦 check_freight_rates()", pulsing=True)
    rates = await check_freight_rates(state["scenario"])
    await publish_tool_result(run_id, AgentId.LOGISTICS, "check_freight_rates", rates)

    rc = dict(state.get("run_context") or {})
    rc["_logistics_rates"] = rates
    return {**state, "run_context": rc}


async def _run_recall_memory(state: LogisticsState) -> LogisticsState:
    run_id   = state["run_id"]
    scenario = state["scenario"]
    sc       = SCENARIO_DEFINITIONS[scenario]

    await publish_state(run_id, AgentId.LOGISTICS, AgentStatus.QUERYING,
                        tool="📚 memory_recall()", pulsing=True)
    memory = await memory_recall(f"{scenario.value} {sc.description[:30]}")
    if memory:
        await publish_tool_result(run_id, AgentId.LOGISTICS, "memory_recall", memory)

    rc = dict(state["run_context"])
    rc["_logistics_memory"] = memory
    return {**state, "run_context": rc}


async def _run_generate(state: LogisticsState) -> LogisticsState:
    run_id     = state["run_id"]
    scenario   = state["scenario"]
    started_at = state.get("started_at") or time.time()
    sc         = SCENARIO_DEFINITIONS[scenario]
    rc         = state["run_context"]
    rates      = rc.get("_logistics_rates", {})
    memory     = rc.get("_logistics_memory")

    await publish_state(run_id, AgentId.LOGISTICS, AgentStatus.PROPOSING,
                        tool="📦 check_freight_rates()", pulsing=True)

    response_text = await stream_gemini(
        run_id, AgentId.LOGISTICS, _build_run_prompt(sc, rates, memory), emit_tokens=True,
    )

    tool_pills = ["📦 check_freight_rates()"]
    if memory:
        tool_pills.append(f'📚 memory_recall("{memory.get("memory_key", "")}")')

    await publish_msg(
        run_id, AgentId.LOGISTICS,
        from_label="LOGISTICS", to_label="→ ORCH",
        timestamp=elapsed(started_at), css_class="al",
        text=response_text, tools=tool_pills,
    )
    await publish_state(run_id, AgentId.LOGISTICS, AgentStatus.PROPOSING,
                        tool="📦 check_freight_rates()", confidence=0.62, pulsing=True)

    rc = dict(rc)
    rc["_logistics_response_text"] = response_text
    return {**state, "run_context": rc}


async def _run_store(state: LogisticsState) -> LogisticsState:
    rc            = dict(state["run_context"])
    rates         = rc.pop("_logistics_rates", {})
    memory        = rc.pop("_logistics_memory", None)
    response_text = rc.pop("_logistics_response_text", "")

    hybrid  = rates.get("hybrid_60_40", {})
    air_key = "air_lax" if "air_lax" in rates else next(iter(rates), "air_lax")
    output  = {
        "recommended_option": "hybrid_60_40",
        "cost_usd":           hybrid.get("cost_usd", 253_000),
        "transit_hours":      hybrid.get("transit_hours", 36),
        "air_option_cost":    rates.get(air_key, {}).get("cost_usd", 450_000),
        "rates":              rates,
        "memory":             memory,
        "response_text":      response_text,
    }
    rc["logistics"] = output
    return {**state, "run_context": rc, "logistics_output": output}


def _build_run_graph():
    g = StateGraph(LogisticsState)
    g.add_node("activate",      _run_activate)
    g.add_node("fetch_rates",   _run_fetch_rates)
    g.add_node("recall_memory", _run_recall_memory)
    g.add_node("generate",      _run_generate)
    g.add_node("store",         _run_store)
    g.set_entry_point("activate")
    g.add_edge("activate",      "fetch_rates")
    g.add_edge("fetch_rates",   "recall_memory")
    g.add_edge("recall_memory", "generate")
    g.add_edge("generate",      "store")
    g.add_edge("store",         END)
    return g.compile()


# ─────────────────────────────────────────────────────────────────────────
# REVISE GRAPH nodes
# ─────────────────────────────────────────────────────────────────────────

async def _revise_activate(state: LogisticsState) -> LogisticsState:
    customs_surcharge = state.get("customs_surcharge", 50_000)

    await publish_state(
        state["run_id"], AgentId.LOGISTICS, AgentStatus.REVISING,
        tool="📦 recalculate_route()", confidence=0.58, pulsing=True,
    )
    revise_result = await recalculate_route(
        base_option="air_lax",
        adjustment=f"customs surcharge +${customs_surcharge // 1000}K",
        extra_cost_usd=customs_surcharge,
        scenario=state["scenario"],
    )
    await publish_tool_result(
        state["run_id"], AgentId.LOGISTICS, "recalculate_route", revise_result
    )

    rc = dict(state.get("run_context") or {})
    rc["_logistics_revise_result"] = revise_result
    return {**state, "run_context": rc}


async def _revise_generate(state: LogisticsState) -> LogisticsState:
    run_id     = state["run_id"]
    scenario   = state["scenario"]
    started_at = state.get("started_at") or time.time()
    sc         = SCENARIO_DEFINITIONS[scenario]

    logistics_out     = state["run_context"].get("logistics", {})
    air_cost          = logistics_out.get("air_option_cost", 450_000)
    customs_surcharge = state.get("customs_surcharge", 50_000)
    challenge         = state.get("challenge", "Customs surcharge applies.")

    response_text = await stream_gemini(
        run_id, AgentId.LOGISTICS,
        _build_revise_prompt(sc, logistics_out, air_cost, customs_surcharge, challenge),
        emit_tokens=True,
    )
    await publish_msg(
        run_id, AgentId.LOGISTICS,
        from_label="LOGISTICS", to_label="→ FINANCE",
        timestamp=elapsed(started_at), css_class="al",
        text=response_text, tools=["📦 recalculate_route()"],
    )
    await publish_state(
        run_id, AgentId.LOGISTICS, AgentStatus.CONSENSUS,
        tool="✅ hybrid_confirmed()", confidence=0.88, pulsing=False,
    )

    rc = dict(state["run_context"])
    rc["_logistics_revision_text"] = response_text
    return {**state, "run_context": rc}


async def _revise_store(state: LogisticsState) -> LogisticsState:
    rc = dict(state["run_context"])
    rc.pop("_logistics_revise_result", None)
    rc.pop("_logistics_revision_text", None)

    logistics = dict(rc.get("logistics", {}))
    logistics["revised_recommendation"] = "hybrid_60_40"
    logistics["consensus"] = True
    rc["logistics"] = logistics

    return {**state, "run_context": rc, "logistics_output": logistics}


def _build_revise_graph():
    g = StateGraph(LogisticsState)
    g.add_node("revise_activate",   _revise_activate)
    g.add_node("generate_revision", _revise_generate)
    g.add_node("store_revision",    _revise_store)
    g.set_entry_point("revise_activate")
    g.add_edge("revise_activate",   "generate_revision")
    g.add_edge("generate_revision", "store_revision")
    g.add_edge("store_revision",    END)
    return g.compile()


# Compiled at import time — stateless, reused across all runs
_RUN_GRAPH    = _build_run_graph()
_REVISE_GRAPH = _build_revise_graph()


# ── Public entry points ───────────────────────────────────────────────────

async def run_logistics_agent(
    run_id: str,
    scenario: ScenarioType,
    run_context: dict,
    start_time: float,
) -> dict:
    """Round-1 main flow. Mutates run_context in-place and returns it."""
    initial: LogisticsState = {
        "run_id":           run_id,
        "scenario":         scenario,
        "run_context":      dict(run_context),
        "started_at":       start_time,
        "agent_id":         AgentId.LOGISTICS,
        "logistics_output": None,
    }
    final = await _RUN_GRAPH.ainvoke(initial)
    run_context.update(final["run_context"])
    return run_context


async def revise_logistics_agent(
    run_id: str,
    scenario: ScenarioType,
    run_context: dict,
    start_time: float,
    challenge: str,
    customs_surcharge: int,
) -> dict:
    """Round-2b revision after Finance challenge. Mutates run_context in-place and returns it."""
    initial: LogisticsState = {
        "run_id":             run_id,
        "scenario":           scenario,
        "run_context":        dict(run_context),
        "started_at":         start_time,
        "agent_id":           AgentId.LOGISTICS,
        "logistics_output":   None,
        "challenge":          challenge,
        "customs_surcharge":  customs_surcharge,
    }
    final = await _REVISE_GRAPH.ainvoke(initial)
    run_context.update(final["run_context"])
    return run_context
