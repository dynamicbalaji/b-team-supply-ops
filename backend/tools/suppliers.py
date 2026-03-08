"""
tools/suppliers.py
──────────────────
Supplier catalog and contract term lookup.
Used by Procurement (query_suppliers) and Sales (query_contract_terms).

Phase 3 replaces with real TursoDB queries.
"""

import asyncio
import random
from core.models import ScenarioType


# ── Supplier catalog ─────────────────────────────────────────────────────

_SUPPLIERS = {
    ScenarioType.PORT_STRIKE: [
        {
            "id":               "SUP-TX-001",
            "name":             "Texas Semiconductor Warehouse",
            "location":         "Dallas, TX",
            "distance_from_la": "1,432 miles",
            "stock_quantity_pct": 80,
            "unit_cost_premium_pct": 12,
            "total_cost_usd":   380_000,
            "transit_hours":    12,
            "cert_hours":       4,
            "risk_level":       "medium",
            "notes":            "80% of order quantity in stock. Remaining 20% needs 4h certification.",
            "contact":          "ops@texsemi.example.com",
        },
        {
            "id":               "SUP-AZ-002",
            "name":             "Tucson Air Logistics Hub",
            "location":         "Tucson, AZ",
            "distance_from_la": "494 miles",
            "stock_quantity_pct": 0,
            "unit_cost_premium_pct": 0,
            "total_cost_usd":   0,
            "transit_hours":    8,
            "cert_hours":       0,
            "risk_level":       "low",
            "notes":            "Backup air routing hub. Not a supplier — used for Hour-20 contingency trigger.",
            "contact":          "ops@tucsonair.example.com",
        },
    ],
    ScenarioType.CUSTOMS_DELAY: [
        {
            "id":               "SUP-KR-001",
            "name":             "Samsung Suwon Component Hub",
            "location":         "Suwon, South Korea",
            "distance_from_la": "5,800 miles",
            "stock_quantity_pct": 100,
            "unit_cost_premium_pct": 8,
            "total_cost_usd":   265_000,
            "transit_hours":    22,
            "cert_hours":       2,
            "risk_level":       "low",
            "notes":            "Full quantity available. Spec-equivalent confirmed. Customs pre-cleared via Busan.",
            "contact":          "logistics@samsungsupply.example.com",
        },
    ],
    ScenarioType.SUPPLIER_BREACH: [
        {
            "id":               "SUP-KR-002",
            "name":             "SK Hynix Emergency Supply",
            "location":         "Icheon, South Korea",
            "distance_from_la": "5,750 miles",
            "stock_quantity_pct": 65,
            "unit_cost_premium_pct": 18,
            "total_cost_usd":   510_000,
            "transit_hours":    20,
            "cert_hours":       6,
            "risk_level":       "medium",
            "notes":            "65% of NVIDIA spec available immediately. Balance in 72h.",
            "contact":          "supply@skhynix.example.com",
        },
        {
            "id":               "SUP-JP-001",
            "name":             "Micron Japan Fab Bridge",
            "location":         "Hiroshima, Japan",
            "distance_from_la": "5,450 miles",
            "stock_quantity_pct": 45,
            "unit_cost_premium_pct": 22,
            "total_cost_usd":   390_000,
            "transit_hours":    18,
            "cert_hours":       8,
            "risk_level":       "medium",
            "notes":            "45% available. 8h cert due to wafer process difference.",
            "contact":          "emergency@micron-jp.example.com",
        },
    ],
}


# ── Contract terms catalog ─────────────────────────────────────────────────

_CONTRACT_TERMS = {
    ScenarioType.PORT_STRIKE: {
        "customer":              "Apple Inc.",
        "contract_ref":          "AAPL-SC-2024-Q3",
        "penalty_clause":        "$2M USD per 48h breach of SLA delivery window",
        "sla_delivery_hours":    48,
        "current_delay_risk_h":  48,
        "extension_terms":       "Customer may grant up to 72h extension at discretion with written notice",
        "extension_accepted":    True,
        "extension_hours":       36,
        "q3_priority_available": True,
        "q3_priority_benefit":   "Q3 allocation bumped to Tier 1 — guaranteed slot in next 3 production cycles",
        "penalty_waived":        True,
        "amendment_ref":         "AAPL-AMD-2024-0312",
        "customer_contact":      "Apple Supply Chain Operations, Cupertino CA",
        "notes":                 "Apple has confirmed 36h extension verbally — amendment pending legal review.",
    },
    ScenarioType.CUSTOMS_DELAY: {
        "customer":              "Samsung Electronics",
        "contract_ref":          "SMSG-SC-2024-Q2",
        "penalty_clause":        "$1.5M USD per 36h breach + production line halt compensation",
        "sla_delivery_hours":    36,
        "current_delay_risk_h":  36,
        "extension_terms":       "Force majeure clause applicable for regulatory holds beyond 48h",
        "extension_accepted":    True,
        "extension_hours":       24,
        "q3_priority_available": False,
        "q3_priority_benefit":   None,
        "penalty_waived":        True,
        "amendment_ref":         "SMSG-FM-2024-0891",
        "customer_contact":      "Samsung Global Procurement, Seoul KR",
        "notes":                 "Force majeure invoked. Samsung waiving penalty. Requesting ETA update by EOD.",
    },
    ScenarioType.SUPPLIER_BREACH: {
        "customer":              "NVIDIA",
        "contract_ref":          "NVDA-SC-2024-Q3",
        "penalty_clause":        "$5M USD + 15% of contract value for unilateral breach",
        "sla_delivery_hours":    72,
        "current_delay_risk_h":  90,
        "extension_terms":       "NVIDIA has approval rights on any supplier substitution",
        "extension_accepted":    False,
        "extension_hours":       0,
        "q3_priority_available": True,
        "q3_priority_benefit":   "NVIDIA willing to accept alt-source if spec certified by their team",
        "penalty_waived":        False,
        "amendment_ref":         None,
        "customer_contact":      "NVIDIA Supply Chain Crisis Desk, Santa Clara CA",
        "notes":                 "NVIDIA requires spec certification before accepting substitution. 6h cert window offered.",
    },
}


# ── Tool functions ────────────────────────────────────────────────────────

async def query_suppliers(
    scenario: ScenarioType,
    location_hint: str = "",
) -> list[dict]:
    """
    Returns alternative suppliers for the scenario.

    Phase 3: tries TursoDB first.
    Falls back to in-memory _SUPPLIERS catalog (with ±5% noise).
    """
    await asyncio.sleep(0.25)

    # ── Phase 3: TursoDB ──────────────────────────────────────────────────
    try:
        import db.turso_client as turso_client
        if turso_client.is_configured():
            db_result = await turso_client.query_suppliers(scenario.value)
            if db_result:
                # Apply noise to costs so each run feels fresh
                for s in db_result:
                    if s["total_cost_usd"]:
                        s["total_cost_usd"] = int(s["total_cost_usd"] * (1 + random.uniform(-0.05, 0.05)))
                return db_result
    except Exception:
        pass

    # ── In-memory fallback ────────────────────────────────────────────────
    suppliers = _SUPPLIERS.get(scenario, [])
    result = []
    for s in suppliers:
        noise = 1 + random.uniform(-0.05, 0.05)
        result.append({
            **s,
            "total_cost_usd": int(s["total_cost_usd"] * noise) if s["total_cost_usd"] else 0,
        })
    return result


async def query_contract_terms(scenario: ScenarioType) -> dict:
    """
    Returns contract terms for the scenario's customer.

    Phase 3: tries TursoDB first.
    Falls back to in-memory _CONTRACT_TERMS.
    """
    await asyncio.sleep(0.2)

    # ── Phase 3: TursoDB ──────────────────────────────────────────────────
    try:
        import db.turso_client as turso_client
        if turso_client.is_configured():
            result = await turso_client.query_contract(scenario.value)
            if result:
                return result
    except Exception:
        pass

    # ── In-memory fallback ────────────────────────────────────────────────
    return _CONTRACT_TERMS.get(scenario, _CONTRACT_TERMS[ScenarioType.PORT_STRIKE])


async def draft_sla_amendment(
    scenario: ScenarioType,
    extension_hours: int,
    new_delivery_plan: str,
) -> dict:
    """
    Drafts an SLA amendment record.
    Returns a confirmation object the Sales agent can cite.
    """
    await asyncio.sleep(0.3)

    terms = _CONTRACT_TERMS.get(scenario, _CONTRACT_TERMS[ScenarioType.PORT_STRIKE])
    return {
        "amendment_id":      terms.get("amendment_ref", f"AMD-{random.randint(1000,9999)}"),
        "customer":          terms["customer"],
        "extension_granted": extension_hours,
        "new_plan":          new_delivery_plan,
        "penalty_waived":    terms["penalty_waived"],
        "status":            "draft_confirmed",
        "next_step":         "Legal countersignature required within 4h",
    }
