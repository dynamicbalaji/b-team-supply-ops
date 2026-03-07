"""
agents/risk.py
──────────────
Risk Agent — Devil's Advocate. The most important agent for the demo.

CRITICAL: This agent fires ONLY AFTER all 4 other agents have reached consensus.
It reads the ENTIRE run_context to find the single biggest failure mode
in the agreed plan.

This is the moment that impresses judges: 4 agents just agreed, the
human is about to click APPROVE, and then Risk Agent says "wait."

Flow:
  1. Show risk_activated event (triggers the red card animation)
  2. Stream Gemini challenge — must find a REAL flaw, not a generic warning
  3. Publish message event with ⚠ prefix
  4. Return the challenge text so Finance can absorb it into contingency
"""

from models import AgentId, AgentStatus, ScenarioType
from scenarios import SCENARIO_DEFINITIONS
from models import RiskActivatedEvent
import redis_client
from agents.base import (
    publish_state, publish_msg,
    stream_gemini, elapsed,
)


PERSONA = """You are the Risk Agent — the Devil's Advocate in a supply chain crisis system.
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


def _build_prompt(
    scenario_desc: str,
    logistics_text: str,
    finance_text: str,
    sales_text: str,
    procurement_text: str,
    hybrid_cost: int,
    hybrid_hours: int,
    customer: str,
    scenario: ScenarioType,
) -> str:

    # Scenario-specific risk knowledge injected to make Gemini precise
    scenario_risk_hints = {
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

    hint = scenario_risk_hints.get(scenario, "")

    return f"""{PERSONA}

CRISIS: {scenario_desc}
CONSENSUS PLAN: Hybrid route — ${hybrid_cost // 1000}K / {hybrid_hours}h / Customer: {customer}

WHAT THE AGENTS AGREED ON:
- LOGISTICS: "{logistics_text[:200]}..."
- FINANCE: "{finance_text[:200]}..."
- SALES: "{sales_text[:200]}..."
- PROCUREMENT: "{procurement_text[:200]}..."

RISK INTELLIGENCE: {hint}

Now find the single most dangerous failure mode in this specific plan.
Be specific — name the exact element that could fail.
State what happens if it fails, then give one concrete mitigation (a backup trigger, time, or action).
Start with: "⚠ Consensus challenge:" """


async def run(
    run_id: str,
    scenario: ScenarioType,
    run_context: dict,
    start_time: float,
) -> dict:
    """
    Executes the Risk Agent. Call ONLY after all 4 agents have reached consensus.
    """
    sc = SCENARIO_DEFINITIONS[scenario]

    logistics = run_context.get("logistics", {})
    finance   = run_context.get("finance", {})
    sales     = run_context.get("sales", {})
    procurement = run_context.get("procurement", {})

    hybrid_cost  = logistics.get("cost_usd", 253_000)
    hybrid_hours = logistics.get("transit_hours", 36)

    # ── 1. Show risk_activated event (red card appears in browser) ────────
    # We publish this BEFORE streaming so the UI reacts immediately
    # The message text will be updated once Gemini responds
    await publish_state(
        run_id, AgentId.RISK, AgentStatus.ACTIVATING,
        tool="🔍 analyze_consensus()", pulsing=True,
    )

    # ── 2. Stream Gemini Devil's Advocate response ─────────────────────
    prompt = _build_prompt(
        scenario_desc=sc.description,
        logistics_text=logistics.get("response_text", "Hybrid recommended."),
        finance_text=finance.get("challenge_text", finance.get("final_text", "Consensus proposed.")),
        sales_text=sales.get("response_text", "Customer confirmed."),
        procurement_text=procurement.get("response_text", "Spot buy option evaluated."),
        hybrid_cost=hybrid_cost,
        hybrid_hours=hybrid_hours,
        customer=sc.customer,
        scenario=scenario,
    )

    challenge_text = await stream_gemini(
        run_id, AgentId.RISK, prompt, emit_tokens=True
    )

    # ── 3. Publish risk_activated with the actual challenge text ──────────
    await redis_client.publish(run_id, RiskActivatedEvent(
        message=challenge_text
    ).model_dump())

    # ── 4. Publish message event ──────────────────────────────────────────
    await publish_msg(
        run_id, AgentId.RISK,
        from_label="RISK AGENT",
        to_label="→ ALL ⚠",
        timestamp=elapsed(start_time),
        css_class="ar",
        text=challenge_text,
        tools=[],
    )

    # Update map status to RISK FLAGGED
    await redis_client.publish(run_id, {
        "type":         "map_update",
        "status":       "RISK FLAGGED",
        "status_color": "#ff3b5c",
    })

    output = {
        "challenge_text": challenge_text,
        "consensus":      False,   # Risk agent never fully "agrees"
    }
    run_context["risk"] = output
    return output
