"""
agents/logistics.py
───────────────────
Logistics Agent — runs parallel with Procurement in Phase 1 of negotiation.

Flow:
  1. Publish ACTIVATING state
  2. Call check_freight_rates() tool — publish ToolEvent
  3. Call memory_recall() — publish ToolEvent with memory badge
  4. Build Gemini prompt with both tool outputs
  5. Stream Gemini response as TokenEvents
  6. Publish final MessageEvent with full text + tool pills
  7. Publish PROPOSING→ confidence state

The agent stores its output in the shared run_context dict so downstream
agents (Finance, Risk) can read it when building their own prompts.
"""

import time
from models import AgentId, AgentStatus, ScenarioType
from scenarios import SCENARIO_DEFINITIONS
from tools.freight import check_freight_rates, memory_recall
from agents.base import (
    publish_state, publish_msg, publish_tool,
    stream_gemini, elapsed,
)


# ── Persona prompt ────────────────────────────────────────────────────────

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
- Reference memory if relevant (cite the date)
- End with a note about what you're uncertain about
- NO bullet points, NO headers, NO markdown formatting
- Write as a live message in a negotiation chat
"""


def _build_prompt(
    scenario_desc: str,
    customer: str,
    budget_cap: int,
    deadline_hours: int,
    rates: dict,
    memory: dict | None,
) -> str:
    rates_summary = "\n".join(
        f"  {k}: ${v.get('cost_usd', 0) // 1000}K / {v.get('transit_hours')}h / {v.get('risk_level')} risk"
        for k, v in rates.items()
    )

    memory_section = ""
    if memory:
        memory_section = (
            f"\nEpisodic memory match: {memory.get('date', 'Unknown date')} — "
            f"{memory.get('crisis', '')}. "
            f"Decision: {memory.get('decision', '')}. "
            f"Saved ${memory.get('saved_usd', 0) // 1000}K."
        )

    return f"""{PERSONA}

CRISIS: {scenario_desc}
CUSTOMER: {customer}
BUDGET CAP: ${budget_cap // 1000}K
DEADLINE: {deadline_hours}h
{memory_section}

FREIGHT OPTIONS FROM check_freight_rates():
{rates_summary}

Write your message to the Orchestrator now. Recommend one primary option and mention the hybrid as backup.
Reference the memory if you recalled one. Flag your biggest uncertainty."""


# ── Main agent function ───────────────────────────────────────────────────

async def run(
    run_id: str,
    scenario: ScenarioType,
    run_context: dict,
    start_time: float,
) -> dict:
    """
    Executes the Logistics agent.

    Args:
        run_id:      Redis queue identifier
        scenario:    Which crisis scenario is running
        run_context: Shared dict — we write our output, other agents read it
        start_time:  time.time() when scenario started (for timestamps)

    Returns:
        Our output dict (also written to run_context["logistics"])
    """
    sc = SCENARIO_DEFINITIONS[scenario]

    # ── 1. Activate ──────────────────────────────────────────────────────
    await publish_state(
        run_id, AgentId.LOGISTICS, AgentStatus.ACTIVATING,
        tool="📡 broadcast_received()", pulsing=True,
    )

    # ── 2. Check freight rates ────────────────────────────────────────────
    await publish_state(
        run_id, AgentId.LOGISTICS, AgentStatus.PROPOSING,
        tool="📦 check_freight_rates()", pulsing=True,
    )

    rates = await check_freight_rates(scenario)
    await publish_tool(run_id, AgentId.LOGISTICS, "check_freight_rates", rates)

    # ── 3. Memory recall ─────────────────────────────────────────────────
    memory_query = f"{scenario.value} port strike"
    memory = await memory_recall(memory_query)

    if memory:
        await publish_tool(run_id, AgentId.LOGISTICS, "memory_recall", memory)

    # ── 4. Build prompt and stream Gemini response ────────────────────────
    prompt = _build_prompt(
        scenario_desc=sc.description,
        customer=sc.customer,
        budget_cap=sc.budget_cap_usd,
        deadline_hours=sc.deadline_hours,
        rates=rates,
        memory=memory,
    )

    response_text = await stream_gemini(run_id, AgentId.LOGISTICS, prompt, emit_tokens=True)

    # ── 5. Publish final message event ───────────────────────────────────
    tool_pills = ["📦 check_freight_rates()"]
    if memory:
        tool_pills.append(f'📚 memory_recall("{memory.get("memory_key", "LA_2024")}")')

    await publish_msg(
        run_id, AgentId.LOGISTICS,
        from_label="LOGISTICS",
        to_label="→ ORCH",
        timestamp=elapsed(start_time),
        css_class="al",
        text=response_text,
        tools=tool_pills,
    )

    # ── 6. Update state with initial confidence ───────────────────────────
    await publish_state(
        run_id, AgentId.LOGISTICS, AgentStatus.PROPOSING,
        tool="📦 check_freight_rates()",
        confidence=0.62,
        pulsing=True,
    )

    # ── 7. Store output for downstream agents ────────────────────────────
    hybrid_rates = rates.get("hybrid_60_40", {})
    output = {
        "recommended_option": "hybrid_60_40",
        "cost_usd":           hybrid_rates.get("cost_usd", 253_000),
        "transit_hours":      hybrid_rates.get("transit_hours", 36),
        "air_option_cost":    rates.get("air_lax", {}).get("cost_usd", 450_000),
        "rates":              rates,
        "memory":             memory,
        "response_text":      response_text,
    }
    run_context["logistics"] = output
    return output


async def revise(
    run_id: str,
    scenario: ScenarioType,
    run_context: dict,
    start_time: float,
    challenge: str,
    customs_surcharge: int,
) -> dict:
    """
    Called after Finance challenges the cost assumption.
    Recalculates and publishes a revised recommendation.
    """
    sc = SCENARIO_DEFINITIONS[scenario]
    logistics_out = run_context.get("logistics", {})
    air_cost = logistics_out.get("air_option_cost", 450_000)
    revised_air = air_cost + customs_surcharge

    await publish_state(
        run_id, AgentId.LOGISTICS, AgentStatus.REVISING,
        tool="📦 recalculate_route()",
        confidence=0.58,
        pulsing=True,
    )

    revise_prompt = f"""{PERSONA}

Finance challenged your ${air_cost // 1000}K air estimate: "{challenge}"
Your recalculation: air total is now ${revised_air // 1000}K — at or over budget cap of ${sc.budget_cap_usd // 1000}K.
The hybrid 60/40 option at ${logistics_out.get('cost_usd', 253_000) // 1000}K / {logistics_out.get('transit_hours', 36)}h now looks significantly better.

Write a 2-sentence acknowledgment confirming the finance agent is correct,
giving the corrected air total, and pivoting your recommendation to the hybrid.
No headers, no bullets, speak as yourself in the chat."""

    response_text = await stream_gemini(run_id, AgentId.LOGISTICS, revise_prompt, emit_tokens=True)

    await publish_msg(
        run_id, AgentId.LOGISTICS,
        from_label="LOGISTICS",
        to_label="→ FINANCE",
        timestamp=elapsed(start_time),
        css_class="al",
        text=response_text,
        tools=[],
    )

    await publish_state(
        run_id, AgentId.LOGISTICS, AgentStatus.CONSENSUS,
        tool="✅ hybrid_confirmed()",
        confidence=0.88,
        pulsing=False,
    )

    run_context["logistics"]["revised_recommendation"] = "hybrid_60_40"
    run_context["logistics"]["consensus"] = True
    return run_context["logistics"]
