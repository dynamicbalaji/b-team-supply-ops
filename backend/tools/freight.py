"""
tools/freight.py
────────────────
Mock freight rate checker and episodic memory recall.

These are called by the Logistics agent during its reasoning.
Phase 3 can swap these for real TursoDB memory queries.

All functions return deterministic data plus ±10% noise so
each run feels slightly different without any external API.
"""

import random
import asyncio
from core.models import ScenarioType


# ── Freight rate catalog ─────────────────────────────────────────────────

_FREIGHT_CATALOG = {
    ScenarioType.PORT_STRIKE: {
        "air_lax": {
            "carrier":       "FedEx Freight Priority",
            "route":         "Shanghai → LAX → Apple Cupertino CA (100% air)",
            "base_cost_usd": 450_000,
            "transit_hours": 24,
            "risk_level":    "low",
            "capacity_pct":  95,
            "notes":         "LAX ground crew availability uncertain during active ILWU strike",
        },
        "sea_oakland": {
            "carrier":       "Hapag-Lloyd Express",
            "route":         "Shanghai → Port of Oakland → Apple Cupertino CA (truck)",
            "base_cost_usd": 190_000,
            "transit_hours": 72,
            "risk_level":    "high",
            "capacity_pct":  60,
            "notes":         "Oakland port also affected by ILWU solidarity action — high risk",
        },
        "hybrid_60_40": {
            "carrier":       "FedEx + Ocean Network Express",
            "route":         "60% air via LAX + 40% sea via Oakland → Apple Cupertino CA",
            "base_cost_usd": 253_000,
            "transit_hours": 36,
            "risk_level":    "medium",
            "capacity_pct":  88,
            "notes":         "Split risk across modes; air leg covers critical components; Hour-20 Tucson backup armed",
        },
    },
    ScenarioType.CUSTOMS_DELAY: {
        "air_direct": {
            "carrier":       "Cathay Pacific Cargo",
            "route":         "Shenzhen → HKG → LAX → Samsung Dallas TX (held — customs dispute)",
            "base_cost_usd": 320_000,
            "transit_hours": 28,
            "risk_level":    "blocked",
            "capacity_pct":  0,
            "notes":         "BLOCKED — same GACC regulatory hold applies at source. Not viable.",
        },
        "air_busan_reroute": {
            "carrier":       "Korean Air Cargo",
            "route":         "Shenzhen → truck → Busan → LAX → Samsung Dallas TX",
            "base_cost_usd": 180_000,
            "transit_hours": 28,
            "risk_level":    "low",
            "capacity_pct":  100,
            "notes":         "Busan routing bypasses Shenzhen GACC hold; ATA carnet pre-clearance at LAX",
        },
        "hybrid_60_40": {
            "carrier":       "Korean Air + COSCO",
            "route":         "60% air via Busan + 40% sea rerouted via Busan → Long Beach",
            "base_cost_usd": 200_000,
            "transit_hours": 32,
            "risk_level":    "medium",
            "capacity_pct":  85,
            "notes":         "Sea leg adds 4h but reduces air freight cost; both routes bypass Shenzhen",
        },
    },
    ScenarioType.SUPPLIER_BREACH: {
        "air_emergency_taiwan": {
            "carrier":       "EVA Air Cargo",
            "route":         "Hsinchu → TPE → LAX → NVIDIA Santa Clara CA (blocked — supplier bankrupt)",
            "base_cost_usd": 680_000,
            "transit_hours": 20,
            "risk_level":    "blocked",
            "capacity_pct":  0,
            "notes":         "BLOCKED — ChipTech bankruptcy; no inventory to ship",
        },
        "alt_supplier_hynix": {
            "carrier":       "Korean Air Cargo",
            "route":         "SK Hynix Suwon → ICN → LAX → NVIDIA Santa Clara CA",
            "base_cost_usd": 510_000,
            "transit_hours": 22,
            "risk_level":    "medium",
            "capacity_pct":  100,
            "notes":         "Full quantity available; NVIDIA spec cert required (6h); Micron Japan parallel cert as backup",
        },
        "hybrid_dual_source": {
            "carrier":       "Korean Air + JAL Cargo",
            "route":         "65% SK Hynix Suwon + 35% Micron Japan Hiroshima → LAX → NVIDIA Santa Clara",
            "base_cost_usd": 580_000,
            "transit_hours": 24,
            "risk_level":    "medium",
            "capacity_pct":  95,
            "notes":         "Dual-source spreads geopolitical risk; both routes via LAX",
        },
    },
}


# ── Episodic memory bank ──────────────────────────────────────────────────

_MEMORY_BANK = {
    "LA_port_strike": {
        "date":           "March 2024",
        "scenario_type":  "port_strike",
        "crisis":         "ILWU walkout — Long Beach + LA ports closed 11 days",
        "decision":       "Hybrid 60/40 air/sea split via LAX + Oakland",
        "outcome":        "Delivered within 38h. Zero penalty.",
        "cost_usd":       272_000,
        "saved_usd":      180_000,
        "key_learning":   "Air-only was at budget cap due to strike customs surcharge. Hybrid beat it by $178K.",
        "confidence":     0.94,
    },
    "Shanghai_customs_2023": {
        "date":           "September 2023",
        "scenario_type":  "customs_delay",
        "crisis":         "SAMR hold on semiconductor exports — 72h freeze",
        "decision":       "Reroute via Busan + ATA carnet pre-clearance at LAX",
        "outcome":        "Cleared in 29h. $1.2M penalty avoided.",
        "cost_usd":       198_000,
        "saved_usd":      145_000,
        "key_learning":   "ATA carnet pre-clearance added 6h but saved 40h of customs processing.",
        "confidence":     0.89,
    },
    "Taiwan_drought_2022": {
        "date":           "July 2022",
        "scenario_type":  "supplier_breach",
        "crisis":         "TSMC production halt — water rationing reduced fab output 35%",
        "decision":       "Dual-source Samsung Suwon + MediaTek Thailand for 60-day bridge",
        "outcome":        "Zero stockout. Production maintained.",
        "cost_usd":       520_000,
        "saved_usd":      420_000,
        "key_learning":   "Alt-sourcing qualification ran parallel to negotiation — saved 2 weeks.",
        "confidence":     0.87,
    },
}


# ── Tool functions ────────────────────────────────────────────────────────

async def check_freight_rates(scenario: ScenarioType) -> dict:
    """
    Returns freight rate options for the scenario.
    Adds ±8% random noise to costs so each run feels fresh.
    Simulates 300ms API latency.
    """
    await asyncio.sleep(0.3)

    catalog = _FREIGHT_CATALOG.get(scenario, _FREIGHT_CATALOG[ScenarioType.PORT_STRIKE])
    result = {}

    for key, option in catalog.items():
        noise = 1 + random.uniform(-0.08, 0.08)
        result[key] = {
            **option,
            "cost_usd": int(option["base_cost_usd"] * noise),
        }
        del result[key]["base_cost_usd"]

    return result


async def memory_recall(query: str) -> dict | None:
    """
    Searches episodic memory for a matching historical incident.

    Phase 3: tries TursoDB first (real persistent memory).
    Falls back to in-memory _MEMORY_BANK when TursoDB is not configured,
    so the demo works without any database credentials.
    """
    await asyncio.sleep(0.15)

    # ── Phase 3: TursoDB lookup ────────────────────────────────────────────
    try:
        import db.turso_client as turso_client
        if turso_client.is_configured():
            query_lower = query.lower()
            # Extract candidate keywords for DB LIKE search
            keywords = [w for w in query_lower.split() if len(w) > 3]
            # Derive scenario type from query keywords for fallback
            if "port" in query_lower or "strike" in query_lower:
                scenario_kw = "port_strike"
            elif "customs" in query_lower or "shanghai" in query_lower:
                scenario_kw = "customs_delay"
            else:
                scenario_kw = "supplier_breach"
            result = await turso_client.recall_memory(keywords, scenario_kw)
            if result:
                return result
    except Exception as exc:
        pass  # Fall through to in-memory bank

    # ── In-memory fallback (always works) ─────────────────────────────────
    query_lower = query.lower()
    for key, memory in _MEMORY_BANK.items():
        key_words = key.lower().replace("_", " ").split()
        if any(word in query_lower for word in key_words):
            return {"memory_key": key, **memory}

    if "port" in query_lower or "strike" in query_lower or "la" in query_lower:
        return {"memory_key": "LA_port_strike", **_MEMORY_BANK["LA_port_strike"]}
    if "customs" in query_lower or "shanghai" in query_lower or "china" in query_lower:
        return {"memory_key": "Shanghai_customs_2023", **_MEMORY_BANK["Shanghai_customs_2023"]}
    if "taiwan" in query_lower or "supplier" in query_lower or "fab" in query_lower:
        return {"memory_key": "Taiwan_drought_2022", **_MEMORY_BANK["Taiwan_drought_2022"]}

    return None


async def recalculate_route(
    base_option: str,
    adjustment: str,
    extra_cost_usd: int,
    scenario: ScenarioType,
) -> dict:
    """
    Recalculates a route after a cost challenge.
    Used by Logistics after Finance challenges an assumption.
    """
    await asyncio.sleep(0.2)

    rates = await check_freight_rates(scenario)
    base = rates.get(base_option, {})

    return {
        "original_option":  base_option,
        "adjustment":        adjustment,
        "extra_cost_usd":    extra_cost_usd,
        "revised_cost_usd":  (base.get("cost_usd", 0) + extra_cost_usd),
        "revised_hours":     base.get("transit_hours", 36),
        "recommendation":    "hybrid_60_40",
        "reason":            f"Air total ${(base.get('cost_usd', 0) + extra_cost_usd) // 1000}K hits budget cap. Hybrid saves ${extra_cost_usd // 1000}K+.",
    }
