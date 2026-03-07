"""
agents/logistics.py  — Phase 3 updated
───────────────────
Logistics Agent — runs parallel with Procurement in Round 1.

Phase 3 changes:
  - publish_tool() replaced with publish_tool_result() so tool outputs
    appear as rich formatted bubbles in the chat (freight table, memory card).
  - Memory badge now fires a full episodic card, not just a pill label.
"""

import time
from models import AgentId, AgentStatus, ScenarioType
from scenarios import SCENARIO_DEFINITIONS
from tools.freight import check_freight_rates, memory_recall, recalculate_route
from agents.base import (
    publish_state, publish_msg, publish_tool_result,
    stream_gemini, elapsed,
)


PERSONA = """You are the Logistics Agent in a real-time supply chain crisis resolution system.
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


def _build_prompt(sc, rates, memory):
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
    return f"""{PERSONA}

CRISIS: {sc.description}
CUSTOMER: {sc.customer}
BUDGET CAP: ${sc.budget_cap_usd // 1000}K
DEADLINE: {sc.deadline_hours}h
{memory_section}

FREIGHT OPTIONS (live from check_freight_rates()):
{rates_summary}

Write your message to the Orchestrator now. Recommend one primary option and mention the hybrid as backup.
Reference the memory date and savings if you recalled one. Flag your biggest single uncertainty."""


async def run(run_id, scenario, run_context, start_time):
    sc = SCENARIO_DEFINITIONS[scenario]

    # 1. Activate
    await publish_state(run_id, AgentId.LOGISTICS, AgentStatus.ACTIVATING,
                        tool="📡 broadcast_received()", pulsing=True)

    # 2. Fetch freight rates — emits rich freight table bubble
    await publish_state(run_id, AgentId.LOGISTICS, AgentStatus.PROPOSING,
                        tool="📦 check_freight_rates()", pulsing=True)
    rates = await check_freight_rates(scenario)
    await publish_tool_result(run_id, AgentId.LOGISTICS, "check_freight_rates", rates)

    # 3. Memory recall — emits episodic memory card bubble (THE badge moment)
    await publish_state(run_id, AgentId.LOGISTICS, AgentStatus.QUERYING,
                        tool="📚 memory_recall()", pulsing=True)
    memory_query = f"{scenario.value} {sc.description[:30]}"
    memory = await memory_recall(memory_query)
    if memory:
        await publish_tool_result(run_id, AgentId.LOGISTICS, "memory_recall", memory)

    # 4. Stream Gemini response
    await publish_state(run_id, AgentId.LOGISTICS, AgentStatus.PROPOSING,
                        tool="📦 check_freight_rates()", pulsing=True)
    response_text = await stream_gemini(
        run_id, AgentId.LOGISTICS, _build_prompt(sc, rates, memory), emit_tokens=True
    )

    # 5. Final message with tool pills
    tool_pills = ["📦 check_freight_rates()"]
    if memory:
        tool_pills.append(f'📚 memory_recall("{memory.get("memory_key", "")}")')
    await publish_msg(run_id, AgentId.LOGISTICS,
                      from_label="LOGISTICS", to_label="→ ORCH",
                      timestamp=elapsed(start_time), css_class="al",
                      text=response_text, tools=tool_pills)

    # 6. Confidence state
    await publish_state(run_id, AgentId.LOGISTICS, AgentStatus.PROPOSING,
                        tool="📦 check_freight_rates()", confidence=0.62, pulsing=True)

    # 7. Store for downstream agents
    hybrid = rates.get("hybrid_60_40", {})
    air_key = "air_lax" if "air_lax" in rates else next(iter(rates), "air_lax")
    output = {
        "recommended_option": "hybrid_60_40",
        "cost_usd":           hybrid.get("cost_usd", 253_000),
        "transit_hours":      hybrid.get("transit_hours", 36),
        "air_option_cost":    rates.get(air_key, {}).get("cost_usd", 450_000),
        "rates":              rates,
        "memory":             memory,
        "response_text":      response_text,
    }
    run_context["logistics"] = output
    return output


async def revise(run_id, scenario, run_context, start_time, challenge, customs_surcharge):
    sc = SCENARIO_DEFINITIONS[scenario]
    logistics_out = run_context.get("logistics", {})
    air_cost     = logistics_out.get("air_option_cost", 450_000)
    revised_air  = air_cost + customs_surcharge

    await publish_state(run_id, AgentId.LOGISTICS, AgentStatus.REVISING,
                        tool="📦 recalculate_route()", confidence=0.58, pulsing=True)

    # Call recalculate_route tool and show result bubble
    revise_result = await recalculate_route(
        base_option="air_lax",
        adjustment=f"customs surcharge +${customs_surcharge // 1000}K",
        extra_cost_usd=customs_surcharge,
        scenario=scenario,
    )
    await publish_tool_result(run_id, AgentId.LOGISTICS, "recalculate_route", revise_result)

    revise_prompt = f"""{PERSONA}

Finance challenged your ${air_cost // 1000}K air estimate: "{challenge}"
recalculate_route() confirms: air total = ${revised_air // 1000}K — at/over budget cap of ${sc.budget_cap_usd // 1000}K.
The hybrid 60/40 option at ${logistics_out.get('cost_usd', 253_000) // 1000}K / {logistics_out.get('transit_hours', 36)}h is now clearly better.

Write a 2-sentence acknowledgment: confirm finance is correct with the revised air total, then pivot your recommendation to hybrid.
No headers, no bullets, speak as yourself in the chat."""

    response_text = await stream_gemini(
        run_id, AgentId.LOGISTICS, revise_prompt, emit_tokens=True
    )
    await publish_msg(run_id, AgentId.LOGISTICS,
                      from_label="LOGISTICS", to_label="→ FINANCE",
                      timestamp=elapsed(start_time), css_class="al",
                      text=response_text, tools=["📦 recalculate_route()"])

    await publish_state(run_id, AgentId.LOGISTICS, AgentStatus.CONSENSUS,
                        tool="✅ hybrid_confirmed()", confidence=0.88, pulsing=False)

    run_context["logistics"]["revised_recommendation"] = "hybrid_60_40"
    run_context["logistics"]["consensus"] = True
    return run_context["logistics"]
