"""
graph/a2a_task_runner.py
─────────────────────────
Routes A2A task requests to the appropriate LangGraph subgraph and returns
a structured A2ATaskResult.

Design principles
─────────────────
1. Every public function receives a *synthetic* run_context built from the
   caller's `inputs` dict, so A2A tasks are fully self-contained — they
   don't require an active /api/runs session.

2. SSE events are still published to Redis under the task's `task_id`.
   An A2A client that wants streaming can open GET /api/stream/{task_id}
   before calling POST /agents/{name}/tasks with the same id in metadata.

3. Each agent exposes a fixed set of "task names" (see SUPPORTED_TASKS below).
   Unrecognised task names fall back to the agent's default full flow so
   unknown callers still get a useful response.

4. The orchestrator is intentionally excluded from A2A direct-task calls —
   it is only reachable via POST /api/runs.  Its card is still discoverable
   at /.well-known/agent-card.json.

Task routing table
──────────────────
  logistics
    check_freight          → _RUN_GRAPH  (fetch_rates only, no Gemini)
    recall_memory          → memory_recall() tool directly
    evaluate_crisis        → full _RUN_GRAPH
    revise_route           → _REVISE_GRAPH (needs challenge + surcharge in inputs)
    * default              → evaluate_crisis

  finance
    run_monte_carlo        → run_monte_carlo() tool directly
    query_customs          → query_customs_rates() tool directly
    challenge_cost         → full _RUN_GRAPH
    propose_consensus      → _CONSENSUS_GRAPH (needs reserve_usd in inputs)
    * default              → challenge_cost

  procurement
    query_suppliers        → query_suppliers() tool directly
    evaluate_spot_buy      → full _GRAPH
    * default              → evaluate_spot_buy

  sales
    lookup_contract        → query_contract_terms() tool directly
    draft_amendment        → full _GRAPH  (contract + amendment)
    negotiate_sla          → full _GRAPH
    * default              → negotiate_sla

  risk
    challenge_consensus    → full _GRAPH
    * default              → challenge_consensus
"""

from __future__ import annotations

import time
import uuid
import logging
from typing import Any

from core.models import ScenarioType, AgentId
from core.scenarios import SCENARIO_DEFINITIONS

log = logging.getLogger("chainguardai.a2a_task_runner")


# ── Supported task names per agent (for validation + docs) ───────────────

SUPPORTED_TASKS: dict[str, list[str]] = {
    "logistics":   ["check_freight", "recall_memory", "evaluate_crisis", "revise_route"],
    "finance":     ["run_monte_carlo", "query_customs", "challenge_cost", "propose_consensus"],
    "procurement": ["query_suppliers", "evaluate_spot_buy"],
    "sales":       ["lookup_contract", "draft_amendment", "negotiate_sla"],
    "risk":        ["challenge_consensus"],
}

# Default task when task name is omitted or unrecognised
_DEFAULT_TASK: dict[str, str] = {
    "logistics":   "evaluate_crisis",
    "finance":     "challenge_cost",
    "procurement": "evaluate_spot_buy",
    "sales":       "negotiate_sla",
    "risk":        "challenge_consensus",
}


# ── Helpers ───────────────────────────────────────────────────────────────

def _resolve_scenario(inputs: dict) -> ScenarioType:
    """
    Pull scenario from inputs["scenario"], defaulting to port_strike.
    Accepts both the enum value string ("port_strike") and display names.
    """
    raw = (inputs.get("scenario") or "port_strike").lower().replace(" ", "_")
    try:
        return ScenarioType(raw)
    except ValueError:
        return ScenarioType.PORT_STRIKE


def _synthetic_run_id(task_id: str | None) -> str:
    """Use caller's task_id as run_id so SSE stream is addressable."""
    return task_id or str(uuid.uuid4())


def _base_run_context(inputs: dict, scenario: ScenarioType) -> dict:
    """
    Build a minimal run_context that satisfies subgraph nodes.
    Merges any caller-supplied context so tasks can be called mid-flow
    (e.g. finance challenge_cost after logistics already ran).
    """
    sc = SCENARIO_DEFINITIONS[scenario]
    base: dict[str, Any] = {
        "scenario":   scenario,
        "budget_cap": sc.budget_cap_usd,
        "deadline_h": sc.deadline_hours,
        "customer":   sc.customer,
    }
    # Caller may supply upstream outputs (e.g. logistics output for finance)
    for key in ("logistics", "finance", "procurement", "sales", "risk"):
        if key in inputs:
            base[key] = inputs[key]
    return base


# ── Logistics task runner ─────────────────────────────────────────────────

async def run_logistics_task(
    task: str,
    inputs: dict,
    task_id: str,
) -> dict[str, Any]:
    from tools.freight import check_freight_rates, memory_recall
    from graph.logistics_agent_graph import run_logistics_agent, revise_logistics_agent

    scenario   = _resolve_scenario(inputs)
    run_id     = _synthetic_run_id(task_id)
    start_time = time.time()
    run_ctx    = _base_run_context(inputs, scenario)

    resolved = task if task in SUPPORTED_TASKS["logistics"] else _DEFAULT_TASK["logistics"]

    if resolved == "check_freight":
        rates = await check_freight_rates(scenario)
        return {
            "task": resolved,
            "tool": "check_freight_rates",
            "outputs": {"rates": rates, "scenario": scenario.value},
            "messages": [
                f"Fetched {len(rates)} freight options for scenario '{scenario.value}'."
            ],
        }

    if resolved == "recall_memory":
        query = inputs.get("query", f"{scenario.value} crisis resolution")
        mem   = await memory_recall(query)
        if mem:
            return {
                "task": resolved,
                "tool": "memory_recall",
                "outputs": {"memory": mem},
                "messages": [
                    f"Found historical match: {mem.get('date', '?')} — "
                    f"{mem.get('crisis', '?')}. Saved ${mem.get('saved_usd', 0):,}."
                ],
            }
        return {
            "task": resolved,
            "tool": "memory_recall",
            "outputs": {"memory": None},
            "messages": ["No episodic memory match found for this query."],
        }

    if resolved == "revise_route":
        challenge         = inputs.get("challenge", "Customs surcharge applies.")
        customs_surcharge = int(inputs.get("customs_surcharge", 50_000))
        await revise_logistics_agent(run_id, scenario, run_ctx, start_time,
                                     challenge=challenge,
                                     customs_surcharge=customs_surcharge)
        logistics = run_ctx.get("logistics", {})
        return {
            "task": resolved,
            "outputs": {
                "recommended_option": logistics.get("revised_recommendation", "hybrid_60_40"),
                "logistics":          logistics,
            },
            "messages": [logistics.get("response_text", "")],
        }

    # Default: evaluate_crisis — full run graph
    await run_logistics_agent(run_id, scenario, run_ctx, start_time)
    logistics = run_ctx.get("logistics", {})
    rates     = logistics.get("rates", {})
    memory    = logistics.get("memory")
    return {
        "task": resolved,
        "outputs": {
            "recommended_option": logistics.get("recommended_option", "hybrid_60_40"),
            "cost_usd":           logistics.get("cost_usd"),
            "transit_hours":      logistics.get("transit_hours"),
            "rates":              rates,
            "memory":             memory,
        },
        "messages": [logistics.get("response_text", "")],
        "metadata": {
            "air_option_cost": logistics.get("air_option_cost"),
            "scenario":        scenario.value,
        },
    }


# ── Finance task runner ───────────────────────────────────────────────────

async def run_finance_task(
    task: str,
    inputs: dict,
    task_id: str,
) -> dict[str, Any]:
    from tools.monte_carlo import run_monte_carlo, query_customs_rates
    from graph.finance_agent_graph import run_finance_agent, propose_consensus_finance_agent

    scenario   = _resolve_scenario(inputs)
    run_id     = _synthetic_run_id(task_id)
    start_time = time.time()
    run_ctx    = _base_run_context(inputs, scenario)

    resolved = task if task in SUPPORTED_TASKS["finance"] else _DEFAULT_TASK["finance"]

    if resolved == "run_monte_carlo":
        base_cost = int(inputs.get("base_cost_usd", 253_000))
        n         = int(inputs.get("iterations", 100))
        result    = await run_monte_carlo(base_cost, n_iterations=n)
        return {
            "task": resolved,
            "tool": "run_monte_carlo",
            "outputs": result,
            "messages": [
                f"Monte Carlo ({n} iterations) on ${base_cost:,}: "
                f"mean=${result.get('mean_usd', 0):,}, "
                f"P10=${result.get('p10_usd', 0):,}, "
                f"P90=${result.get('p90_usd', 0):,}, "
                f"CI={result.get('confidence_interval', 0):.0%}."
            ],
        }

    if resolved == "query_customs":
        data = await query_customs_rates(scenario)
        surcharge = data.get("expedited_strike_total_usd",
                    data.get("expedited_usd", 28_000))
        return {
            "task": resolved,
            "tool": "query_customs_rates",
            "outputs": data,
            "messages": [
                f"Customs rates for '{scenario.value}': "
                f"standard=${data.get('standard_usd', 0):,}, "
                f"expedited=${data.get('expedited_usd', 0):,}. "
                f"{data.get('notes', '')}"
            ],
        }

    if resolved == "propose_consensus":
        reserve = int(inputs.get("reserve_usd", 20_000))
        await propose_consensus_finance_agent(run_id, scenario, run_ctx,
                                              start_time, reserve_usd=reserve)
        finance = run_ctx.get("finance", {})
        return {
            "task": resolved,
            "outputs": {
                "authorised_total": finance.get("authorised_total"),
                "reserve_usd":      reserve,
                "confidence":       finance.get("mc_result", {}).get("confidence_interval"),
                "finance":          finance,
            },
            "messages": [finance.get("response_text", "")],
        }

    # Default: challenge_cost — full _RUN_GRAPH
    # Seed run_context with a logistics stub if not provided, so the
    # compute node has something to work with.
    if "logistics" not in run_ctx:
        run_ctx["logistics"] = {
            "recommended_option": "hybrid_60_40",
            "cost_usd":           inputs.get("hybrid_cost_usd", 253_000),
            "air_option_cost":    inputs.get("air_cost_usd", 450_000),
            "response_text":      inputs.get("logistics_text",
                                             "Hybrid 60/40 recommended at $253K / 36h."),
        }
    await run_finance_agent(run_id, scenario, run_ctx, start_time)
    finance  = run_ctx.get("finance", {})
    mc       = finance.get("mc_result", {})
    customs  = finance.get("customs_data", {})
    return {
        "task": resolved,
        "outputs": {
            "challenge_text":    finance.get("challenge_text"),
            "customs_surcharge": finance.get("customs_surcharge"),
            "hybrid_cost":       finance.get("hybrid_cost"),
            "monte_carlo":       mc,
        },
        "messages": [finance.get("response_text", "")],
        "metadata": {
            "customs_notes": customs.get("notes"),
            "scenario":      scenario.value,
        },
    }


# ── Procurement task runner ───────────────────────────────────────────────

async def run_procurement_task(
    task: str,
    inputs: dict,
    task_id: str,
) -> dict[str, Any]:
    from tools.suppliers import query_suppliers
    from graph.procurement_agent_graph import run_procurement_agent

    scenario   = _resolve_scenario(inputs)
    run_id     = _synthetic_run_id(task_id)
    start_time = time.time()
    run_ctx    = _base_run_context(inputs, scenario)

    resolved = task if task in SUPPORTED_TASKS["procurement"] else _DEFAULT_TASK["procurement"]

    if resolved == "query_suppliers":
        location = inputs.get("location_hint", "dallas")
        suppliers = await query_suppliers(scenario, location_hint=location)
        viable    = [s for s in suppliers if s.get("total_cost_usd", 0) > 0]
        primary   = viable[0] if viable else {}
        return {
            "task": resolved,
            "tool": "query_suppliers",
            "outputs": {
                "suppliers": suppliers,
                "primary":   primary,
                "count":     len(viable),
            },
            "messages": [
                f"Found {len(viable)} viable suppliers near '{location}'. "
                + (
                    f"Best: {primary.get('name')} — "
                    f"${primary.get('total_cost_usd', 0):,} / "
                    f"{primary.get('transit_hours')}h / "
                    f"{primary.get('stock_quantity_pct')}% qty."
                    if primary else "No viable options."
                )
            ],
        }

    # Default: evaluate_spot_buy — full graph
    await run_procurement_agent(run_id, scenario, run_ctx, start_time)
    procurement = run_ctx.get("procurement", {})
    primary     = procurement.get("primary_option", {})
    return {
        "task": resolved,
        "outputs": {
            "cost_usd":     procurement.get("cost_usd"),
            "quantity_pct": procurement.get("quantity_pct"),
            "cert_hours":   procurement.get("cert_hours"),
            "primary":      primary,
            "shortfall":    procurement.get("quantity_pct", 100) < 100,
        },
        "messages": [procurement.get("response_text", "")],
        "metadata": {
            "supplier_name":  primary.get("name"),
            "supplier_location": primary.get("location"),
            "scenario":      scenario.value,
        },
    }


# ── Sales task runner ─────────────────────────────────────────────────────

async def run_sales_task(
    task: str,
    inputs: dict,
    task_id: str,
) -> dict[str, Any]:
    from tools.suppliers import query_contract_terms
    from graph.sales_agent_graph import run_sales_agent

    scenario   = _resolve_scenario(inputs)
    run_id     = _synthetic_run_id(task_id)
    start_time = time.time()
    run_ctx    = _base_run_context(inputs, scenario)

    resolved = task if task in SUPPORTED_TASKS["sales"] else _DEFAULT_TASK["sales"]

    if resolved == "lookup_contract":
        contract = await query_contract_terms(scenario)
        sc       = SCENARIO_DEFINITIONS[scenario]
        return {
            "task": resolved,
            "tool": "query_contract_terms",
            "outputs": contract,
            "messages": [
                f"{sc.customer} contract: "
                f"SLA {contract.get('sla_hours', '?')}h, "
                f"penalty ${contract.get('penalty_usd', 0):,}, "
                f"extension {contract.get('extension_hours', '?')}h available="
                f"{contract.get('extension_accepted', False)}."
            ],
        }

    # Default: negotiate_sla / draft_amendment — full graph
    # Seed with a logistics stub so the amendment node has hybrid cost/hours.
    if "logistics" not in run_ctx:
        run_ctx["logistics"] = {
            "cost_usd":      inputs.get("hybrid_cost_usd", 253_000),
            "transit_hours": inputs.get("hybrid_hours", 36),
        }
    await run_sales_agent(run_id, scenario, run_ctx, start_time)
    sales     = run_ctx.get("sales", {})
    amendment = sales.get("amendment", {})
    contract  = sales.get("contract", {})
    return {
        "task": resolved,
        "outputs": {
            "amendment_id":      amendment.get("amendment_id"),
            "extension_granted": amendment.get("extension_granted_hours",
                                  sales.get("extension_hours")),
            "penalty_waived":    sales.get("penalty_waived"),
            "customer":          sales.get("customer"),
            "next_step":         amendment.get("next_step"),
        },
        "messages": [sales.get("response_text", "")],
        "metadata": {
            "contract_ref":    contract.get("contract_ref"),
            "q3_benefit":      contract.get("q3_priority_benefit"),
            "scenario":        scenario.value,
        },
    }


# ── Risk task runner ──────────────────────────────────────────────────────

async def run_risk_task(
    task: str,
    inputs: dict,
    task_id: str,
) -> dict[str, Any]:
    from graph.risk_agent_graph import run_risk_agent

    scenario   = _resolve_scenario(inputs)
    run_id     = _synthetic_run_id(task_id)
    start_time = time.time()
    run_ctx    = _base_run_context(inputs, scenario)

    # Risk needs a plausible consensus in run_context to challenge.
    # Build stubs from inputs so callers can inject real upstream data.
    if "logistics" not in run_ctx:
        run_ctx["logistics"] = {
            "recommended_option": "hybrid_60_40",
            "cost_usd":           inputs.get("hybrid_cost_usd", 253_000),
            "transit_hours":      inputs.get("hybrid_hours", 36),
            "response_text":      "Hybrid 60/40 recommended.",
        }
    if "finance" not in run_ctx:
        run_ctx["finance"] = {
            "challenge_text": "Customs surcharge confirmed. Hybrid within budget.",
            "hybrid_cost":    inputs.get("hybrid_cost_usd", 253_000),
        }
    if "sales" not in run_ctx:
        run_ctx["sales"] = {
            "extension_hours": 36,
            "penalty_waived":  True,
            "customer":        SCENARIO_DEFINITIONS[scenario].customer,
        }

    await run_risk_agent(run_id, scenario, run_ctx, start_time)
    risk = run_ctx.get("risk", {})
    return {
        "task": "challenge_consensus",
        "outputs": {
            "challenge_text": risk.get("challenge_text"),
            "consensus":      False,
        },
        "messages": [risk.get("challenge_text", "")],
        "metadata": {"scenario": scenario.value},
    }


# ── Dispatch table ────────────────────────────────────────────────────────

_RUNNERS = {
    "logistics":   run_logistics_task,
    "finance":     run_finance_task,
    "procurement": run_procurement_task,
    "sales":       run_sales_task,
    "risk":        run_risk_task,
}


async def dispatch(
    agent_name: str,
    task: str,
    inputs: dict,
    task_id: str,
) -> dict[str, Any]:
    """
    Entry point called by the FastAPI route.
    Returns the raw outputs dict; the route wraps it in A2ATaskResult.
    Raises ValueError for unknown agents.
    """
    runner = _RUNNERS.get(agent_name)
    if runner is None:
        raise ValueError(
            f"No A2A task runner for agent '{agent_name}'. "
            f"Available: {list(_RUNNERS)}"
        )
    return await runner(task, inputs, task_id)
