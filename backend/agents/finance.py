"""
agents/finance.py  — Phase 3 updated
─────────────────
Finance Agent — runs after Logistics proposes.

Phase 3 changes:
  - Monte Carlo result now appears as rich histogram card in chat.
  - Customs rates appear as formatted table bubble.
  - Both tool calls use publish_tool_result().
"""

import asyncio
from models import AgentId, AgentStatus, ScenarioType
from scenarios import SCENARIO_DEFINITIONS
from tools.monte_carlo import run_monte_carlo, query_customs_rates
from agents.base import (
    publish_state, publish_msg, publish_tool_result,
    stream_gemini, elapsed,
)


PERSONA = """You are the Finance Agent in a real-time supply chain crisis resolution system.
You are part of a 5-agent team negotiating the fastest, safest resolution to a P0 crisis.

Your personality:
- The most analytical agent. You question every number.
- You run Monte Carlo simulations — you speak in confidence intervals, not point estimates.
- You challenge assumptions aggressively but constructively.
- Brief and sharp. A few precise sentences, then your conclusion. No fluff.
- No bullet points. No headers. Chat message format only.
"""


def _build_challenge_prompt(sc, logistics_text, logistics_cost, customs_data, mc_result):
    surcharge = customs_data.get("expedited_strike_total_usd",
                customs_data.get("expedited_usd", 28_000))
    revised_air = logistics_cost + surcharge
    return f"""{PERSONA}

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


def _build_consensus_prompt(sc, hybrid_cost, reserve, confidence, mc_result, risk_challenge=None):
    risk_section = ""
    if risk_challenge:
        risk_section = f"\nRISK AGENT CHALLENGED: \"{risk_challenge[:200]}\"\nAbsorbing +${reserve // 1000}K contingency reserve for backup trigger."
    return f"""{PERSONA}

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


async def run(run_id, scenario, run_context, start_time):
    sc = SCENARIO_DEFINITIONS[scenario]
    logistics     = run_context.get("logistics", {})
    logistics_cost = logistics.get("air_option_cost", 450_000)
    logistics_text = logistics.get("response_text", "Air via LAX recommended.")
    hybrid_cost    = logistics.get("cost_usd", 253_000)

    # 1. Activate
    await publish_state(run_id, AgentId.FINANCE, AgentStatus.ACTIVATING,
                        tool="📡 broadcast_received()", pulsing=True)
    await publish_state(run_id, AgentId.FINANCE, AgentStatus.CALCULATING,
                        tool="📊 run_monte_carlo(100)", pulsing=True)

    # 2. Monte Carlo + customs in parallel — both become rich bubbles
    mc_result, customs_data = await asyncio.gather(
        run_monte_carlo(hybrid_cost, n_iterations=100),
        query_customs_rates(scenario),
    )
    await publish_tool_result(run_id, AgentId.FINANCE, "run_monte_carlo", mc_result)
    await publish_tool_result(run_id, AgentId.FINANCE, "query_customs_rates", customs_data)

    # 3. Challenge Logistics
    challenge_text = await stream_gemini(
        run_id, AgentId.FINANCE,
        _build_challenge_prompt(sc, logistics_text, logistics_cost, customs_data, mc_result),
        emit_tokens=True,
    )
    await publish_msg(run_id, AgentId.FINANCE,
                      from_label="FINANCE", to_label="→ LOGISTICS",
                      timestamp=elapsed(start_time), css_class="af",
                      text=challenge_text,
                      tools=["📊 run_monte_carlo(100)", "💰 query_customs_rates()"])

    surcharge = customs_data.get("expedited_strike_total_usd",
                customs_data.get("expedited_usd", 28_000))
    output = {
        "mc_result":         mc_result,
        "customs_data":      customs_data,
        "customs_surcharge": surcharge,
        "challenge_text":    challenge_text,
        "hybrid_cost":       hybrid_cost,
        "consensus":         False,
        "response_text":     challenge_text,
    }
    run_context["finance"] = output
    return output


async def propose_consensus(run_id, scenario, run_context, start_time, reserve_usd=20_000):
    sc = SCENARIO_DEFINITIONS[scenario]
    finance     = run_context.get("finance", {})
    mc_result   = finance.get("mc_result", {})
    hybrid_cost = finance.get("hybrid_cost", 253_000)
    confidence  = mc_result.get("confidence_interval", 0.94)
    risk_challenge = run_context.get("risk", {}).get("challenge_text")

    await publish_state(run_id, AgentId.FINANCE, AgentStatus.FINALISING,
                        tool="✅ propose_consensus()", pulsing=True)

    final_text = await stream_gemini(
        run_id, AgentId.FINANCE,
        _build_consensus_prompt(sc, hybrid_cost, reserve_usd, confidence, mc_result, risk_challenge),
        emit_tokens=True,
    )
    await publish_msg(run_id, AgentId.FINANCE,
                      from_label="FINANCE", to_label="→ ALL",
                      timestamp=elapsed(start_time), css_class="af",
                      text=final_text, tools=["✅ propose_consensus()"])

    await publish_state(run_id, AgentId.FINANCE, AgentStatus.CONSENSUS,
                        tool="✅ propose_consensus()", confidence=confidence, pulsing=False)

    run_context["finance"]["consensus"]  = True
    run_context["finance"]["final_text"] = final_text
    run_context["finance"]["total_cost"] = hybrid_cost + reserve_usd
    return run_context["finance"]
