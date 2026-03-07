"""
graph/risk_agent_graph.py
──────────────────────────
Risk Agent (Devil's Advocate) as a LangGraph subgraph.

No tool calls — simplest possible graph:
  activate → generate → store → END

The activate node fires the risk_activated SSE event so the red card
animation in the browser triggers before Gemini starts streaming.
The generate node streams tokens and then publishes the full
risk_activated event with the final text + the MessageEvent.

Public entry point (signature identical to agents/risk.py):
  run_risk_agent(run_id, scenario, run_context, start_time) -> dict
"""

from __future__ import annotations

import time
from typing import Any, Dict

from langgraph.graph import StateGraph, END

import redis_client
from models import AgentId, AgentStatus, RiskActivatedEvent, ScenarioType
from scenarios import SCENARIO_DEFINITIONS
from agents.base import (
    publish_state,
    publish_msg,
    stream_gemini,
    elapsed,
)
from graph.state import RunGraphState


# ── Agent-local state ─────────────────────────────────────────────────────

class RiskState(RunGraphState, total=False):
    """RunGraphState + Risk-private fields."""
    agent_id: AgentId
    risk_output: Dict[str, Any] | None


# ── Persona + prompt builder ──────────────────────────────────────────────

_PERSONA = """You are the Risk Agent — the Devil's Advocate in a supply chain crisis system.
You activate ONLY after all other agents have reached consensus.

Your ONLY job: find the single biggest failure mode in the agreed plan.

Rules:
- You do NOT agree with the consensus. That is not your role.
- You find ONE specific, concrete risk — not a generic "things might go wrong" warning.
- You name a specific element: a company, a location, a person, a system, a dependency.
- You state severity: what happens if this fails?
- You give ONE mitigation: a specific backup trigger or contingency action.
- Format: "⚠ Consensus challenge: [specific risk]. [Severity if it fails]. Recommend [specific mitigation]."
- Maximum 3 sentences. Be blunt. No softening language.
"""

_SCENARIO_RISK_HINTS = {
    ScenarioType.PORT_STRIKE: (
        "Known risk factor: LAX ground crew availability during ILWU solidarity actions. "
        "The hybrid plan depends on air freight via LAX, but LAX ramp workers may honor "
        "ILWU picket lines. This is a real operational risk that has occurred before."
    ),
    ScenarioType.CUSTOMS_DELAY: (
        "Known risk factor: The Busan reroute relies on customs pre-clearance timing. "
        "If the ATA carnet paperwork is delayed by even 2 hours, the entire 32h window collapses. "
        "There is a single person at the Busan customs office who signs off on express carnet processing."
    ),
    ScenarioType.SUPPLIER_BREACH: (
        "Known risk factor: The alt-source from Korea requires NVIDIA spec certification. "
        "NVIDIA's certification team is in Santa Clara — if the 6h cert window overlaps with "
        "their Friday 4pm cutoff, the next window is Monday morning, adding 60+ hours."
    ),
}


def _build_prompt(sc, run_context: dict, scenario: ScenarioType) -> str:
    logistics   = run_context.get("logistics", {})
    finance     = run_context.get("finance", {})
    sales       = run_context.get("sales", {})
    procurement = run_context.get("procurement", {})

    hybrid_cost  = logistics.get("cost_usd", 253_000)
    hybrid_hours = logistics.get("transit_hours", 36)
    hint         = _SCENARIO_RISK_HINTS.get(scenario, "")

    return f"""{_PERSONA}

CRISIS: {sc.description}
CONSENSUS PLAN: Hybrid route — ${hybrid_cost // 1000}K / {hybrid_hours}h / Customer: {sc.customer}

WHAT THE AGENTS AGREED ON:
- LOGISTICS: "{logistics.get('response_text', 'Hybrid recommended.')[:200]}..."
- FINANCE: "{finance.get('challenge_text', finance.get('final_text', 'Consensus proposed.'))[:200]}..."
- SALES: "{sales.get('response_text', 'Customer confirmed.')[:200]}..."
- PROCUREMENT: "{procurement.get('response_text', 'Spot buy option evaluated.')[:200]}..."

RISK INTELLIGENCE: {hint}

Now find the single most dangerous failure mode in this specific plan.
Be specific — name the exact element that could fail.
State what happens if it fails, then give one concrete mitigation (a backup trigger, time, or action).
Start with: "⚠ Consensus challenge:" """


# ── Nodes ─────────────────────────────────────────────────────────────────

async def _node_activate(state: RiskState) -> RiskState:
    """Publish ACTIVATING state so the risk card appears in the browser immediately."""
    await publish_state(
        state["run_id"], AgentId.RISK, AgentStatus.ACTIVATING,
        tool="🔍 analyze_consensus()", pulsing=True,
    )
    return state


async def _node_generate(state: RiskState) -> RiskState:
    """Stream the Devil's Advocate challenge, then emit risk_activated + MessageEvent."""
    run_id     = state["run_id"]
    scenario   = state["scenario"]
    started_at = state.get("started_at") or time.time()
    sc         = SCENARIO_DEFINITIONS[scenario]

    challenge_text = await stream_gemini(
        run_id, AgentId.RISK,
        _build_prompt(sc, state["run_context"], scenario),
        emit_tokens=True,
    )

    # risk_activated carries the full text for the red banner
    await redis_client.publish(run_id, RiskActivatedEvent(
        message=challenge_text
    ).model_dump())

    await publish_msg(
        run_id, AgentId.RISK,
        from_label="RISK AGENT", to_label="→ ALL ⚠",
        timestamp=elapsed(started_at), css_class="ar",
        text=challenge_text, tools=[],
    )
    await redis_client.publish(run_id, {
        "type":         "map_update",
        "status":       "RISK FLAGGED",
        "status_color": "#ff3b5c",
    })

    rc = dict(state["run_context"])
    rc["_risk_challenge_text"] = challenge_text
    return {**state, "run_context": rc}


async def _node_store(state: RiskState) -> RiskState:
    rc             = dict(state["run_context"])
    challenge_text = rc.pop("_risk_challenge_text", "")

    output = {
        "challenge_text": challenge_text,
        "consensus":      False,   # Risk agent never fully agrees
    }
    rc["risk"] = output
    return {**state, "run_context": rc, "risk_output": output}


# ── Graph assembly ────────────────────────────────────────────────────────

def _build_graph():
    g = StateGraph(RiskState)
    g.add_node("activate", _node_activate)
    g.add_node("generate", _node_generate)
    g.add_node("store",    _node_store)
    g.set_entry_point("activate")
    g.add_edge("activate", "generate")
    g.add_edge("generate", "store")
    g.add_edge("store",    END)
    return g.compile()


_GRAPH = _build_graph()


# ── Public entry point ────────────────────────────────────────────────────

async def run_risk_agent(
    run_id: str,
    scenario: ScenarioType,
    run_context: dict,
    start_time: float,
) -> dict:
    """Round-4 Devil's Advocate. Mutates run_context in-place and returns it."""
    initial: RiskState = {
        "run_id":      run_id,
        "scenario":    scenario,
        "run_context": dict(run_context),
        "started_at":  start_time,
        "agent_id":    AgentId.RISK,
        "risk_output": None,
    }
    final = await _GRAPH.ainvoke(initial)
    run_context.update(final["run_context"])
    return run_context
