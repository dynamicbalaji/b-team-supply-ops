"""
agents/finance.py
─────────────────
Finance Agent — activates after Logistics proposes, reads their output.

Flow:
  1. CALCULATING state — run Monte Carlo + query customs rates simultaneously
  2. Publish both ToolEvents
  3. Stream "challenge" message to Logistics (challenges customs assumption)
  4. After Logistics revises: publish CONSENSUS state + final recommendation
  5. After Risk Agent: absorb contingency, propose final approval
"""

import asyncio
from models import AgentId, AgentStatus, ScenarioType
from scenarios import SCENARIO_DEFINITIONS
from tools.monte_carlo import run_monte_carlo, query_customs_rates
from agents.base import (
    publish_state, publish_msg, publish_tool,
    stream_gemini, elapsed,
)


PERSONA = """You are the Finance Agent in a real-time supply chain crisis resolution system.
You are part of a 5-agent team negotiating the fastest, safest resolution to a P0 crisis.

Your personality:
- You are the most analytical agent. You question every number.
- You run Monte Carlo simulations to understand cost uncertainty, not just point estimates.
- You challenge assumptions aggressively but constructively — you want the BEST answer, not to win.
- You speak in terms of confidence intervals, percentiles, and expected value.
- You are brief. A few sharp sentences, then your conclusion. No fluff.
- No bullet points. No headers. Chat message format only.
"""


def _build_challenge_prompt(
    scenario_desc: str,
    logistics_text: str,
    logistics_cost: int,
    customs_data: dict,
    mc_result: dict,
    budget_cap: int,
) -> str:
    surcharge = customs_data.get("expedited_strike_total_usd",
                customs_data.get("expedited_usd", 28_000))
    revised_air = logistics_cost + surcharge

    return f"""{PERSONA}

CRISIS: {scenario_desc}
BUDGET CAP: ${budget_cap // 1000}K

LOGISTICS AGENT SAID: "{logistics_text}"
They quoted ${logistics_cost // 1000}K for the air option.

YOUR CUSTOMS RATE DATA: expedited + strike surcharge = ${surcharge // 1000}K extra.
That means their air total is actually ${revised_air // 1000}K.

YOUR MONTE CARLO (100 iterations on the hybrid option):
  Mean: ${mc_result['mean_usd'] // 1000}K
  P10:  ${mc_result['p10_usd'] // 1000}K  (best case)
  P90:  ${mc_result['p90_usd'] // 1000}K  (worst case)
  Confidence interval: {int(mc_result['confidence_interval'] * 100)}%

Write a 2-3 sentence message to the Logistics agent.
Challenge their cost assumption with the customs surcharge data.
Ask if they included expedited customs at LAX during strike conditions.
Do not reveal the Monte Carlo result yet — just challenge the assumption."""


def _build_consensus_prompt(
    scenario_desc: str,
    hybrid_cost: int,
    reserve: int,
    confidence: float,
    mc_result: dict,
    risk_challenge: str | None = None,
) -> str:
    risk_section = ""
    if risk_challenge:
        risk_section = f"""
RISK AGENT CHALLENGED: "{risk_challenge}"
You are absorbing a +${reserve // 1000}K contingency reserve for the backup trigger."""

    return f"""{PERSONA}

CRISIS: {scenario_desc}

FINAL NUMBERS CONFIRMED:
  Hybrid option: ${hybrid_cost // 1000}K
  Reserve for contingency: +${reserve // 1000}K
  Total authorised: ${(hybrid_cost + reserve) // 1000}K
  Monte Carlo confidence: {int(confidence * 100)}%
{risk_section}

Write a 2-3 sentence final recommendation message addressed to ALL agents.
State the final cost, include the confidence interval, acknowledge the risk contingency if present.
End by proposing approval. Speak like you are closing the negotiation."""


async def run(
    run_id: str,
    scenario: ScenarioType,
    run_context: dict,
    start_time: float,
) -> dict:
    """
    Executes the Finance agent's challenge phase.
    Called AFTER Logistics has published its proposal (run_context["logistics"] exists).
    """
    sc = SCENARIO_DEFINITIONS[scenario]
    logistics = run_context.get("logistics", {})
    logistics_cost = logistics.get("air_option_cost", 450_000)
    logistics_text = logistics.get("response_text", "Air via LAX recommended.")
    hybrid_cost = logistics.get("cost_usd", 253_000)

    # ── 1. Activate + run tools in parallel ──────────────────────────────
    await publish_state(
        run_id, AgentId.FINANCE, AgentStatus.ACTIVATING,
        tool="📡 broadcast_received()", pulsing=True,
    )

    await publish_state(
        run_id, AgentId.FINANCE, AgentStatus.CALCULATING,
        tool="📊 run_monte_carlo(100)", pulsing=True,
    )

    # Run Monte Carlo and customs query concurrently
    mc_result, customs_data = await asyncio.gather(
        run_monte_carlo(hybrid_cost, n_iterations=100),
        query_customs_rates(scenario),
    )

    await publish_tool(run_id, AgentId.FINANCE, "run_monte_carlo", mc_result)
    await publish_tool(run_id, AgentId.FINANCE, "query_customs_rates", customs_data)

    # ── 2. Challenge Logistics ────────────────────────────────────────────
    challenge_prompt = _build_challenge_prompt(
        scenario_desc=sc.description,
        logistics_text=logistics_text,
        logistics_cost=logistics_cost,
        customs_data=customs_data,
        mc_result=mc_result,
        budget_cap=sc.budget_cap_usd,
    )

    challenge_text = await stream_gemini(
        run_id, AgentId.FINANCE, challenge_prompt, emit_tokens=True
    )

    await publish_msg(
        run_id, AgentId.FINANCE,
        from_label="FINANCE",
        to_label="→ LOGISTICS",
        timestamp=elapsed(start_time),
        css_class="af",
        text=challenge_text,
        tools=["📊 run_monte_carlo(100)", "💰 query_customs_rates()"],
    )

    # Store for orchestrator
    surcharge = customs_data.get("expedited_strike_total_usd",
               customs_data.get("expedited_usd", 28_000))
    output = {
        "mc_result":        mc_result,
        "customs_data":     customs_data,
        "customs_surcharge": surcharge,
        "challenge_text":   challenge_text,
        "hybrid_cost":      hybrid_cost,
        "consensus":        False,
        "response_text":    challenge_text,
    }
    run_context["finance"] = output
    return output


async def propose_consensus(
    run_id: str,
    scenario: ScenarioType,
    run_context: dict,
    start_time: float,
    reserve_usd: int = 20_000,
) -> dict:
    """
    Called after Logistics revises AND (optionally) after Risk agent fires.
    Publishes the final recommendation and CONSENSUS state.
    """
    sc = SCENARIO_DEFINITIONS[scenario]
    finance = run_context.get("finance", {})
    mc_result = finance.get("mc_result", {})
    hybrid_cost = finance.get("hybrid_cost", 253_000)
    confidence = mc_result.get("confidence_interval", 0.94)

    risk_challenge = None
    if run_context.get("risk", {}).get("challenge_text"):
        risk_challenge = run_context["risk"]["challenge_text"]

    await publish_state(
        run_id, AgentId.FINANCE, AgentStatus.FINALISING,
        tool="✅ propose_consensus()", pulsing=True,
    )

    final_prompt = _build_consensus_prompt(
        scenario_desc=sc.description,
        hybrid_cost=hybrid_cost,
        reserve=reserve_usd,
        confidence=confidence,
        mc_result=mc_result,
        risk_challenge=risk_challenge,
    )

    final_text = await stream_gemini(
        run_id, AgentId.FINANCE, final_prompt, emit_tokens=True
    )

    await publish_msg(
        run_id, AgentId.FINANCE,
        from_label="FINANCE",
        to_label="→ ALL",
        timestamp=elapsed(start_time),
        css_class="af",
        text=final_text,
        tools=["✅ propose_consensus()"],
    )

    await publish_state(
        run_id, AgentId.FINANCE, AgentStatus.CONSENSUS,
        tool="✅ propose_consensus()",
        confidence=confidence,
        pulsing=False,
    )

    run_context["finance"]["consensus"] = True
    run_context["finance"]["final_text"] = final_text
    run_context["finance"]["total_cost"] = hybrid_cost + reserve_usd
    return run_context["finance"]
