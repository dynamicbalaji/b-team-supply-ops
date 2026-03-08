"""
tools/monte_carlo.py
────────────────────
Monte Carlo cost simulation for the Finance agent.

Runs N iterations drawing from a normal distribution around the base cost.
Returns a 22-bucket histogram that the D3 chart in the Decision Matrix tab
renders directly — no extra API call needed from the frontend.

Also provides query_customs_rates() used to challenge the Logistics agent's
LAX cost assumption.
"""

import random
import asyncio
import math
from core.models import ScenarioType


# ── Customs rate catalog ─────────────────────────────────────────────────

_CUSTOMS_RATES = {
    ScenarioType.PORT_STRIKE: {
        "standard_usd":               12_000,
        "expedited_usd":              28_000,
        "strike_surcharge_usd":       22_000,
        "expedited_strike_total_usd": 50_000,
        "processing_hours_standard":  6,
        "processing_hours_expedited": 2,
        "notes": "ILWU strike activates Tier-3 surcharge. Expedited + strike = $50K all-in.",
    },
    ScenarioType.CUSTOMS_DELAY: {
        "standard_usd":          8_000,
        "expedited_usd":         18_000,
        "regulatory_hold_usd":   0,        # Hold means NO customs can clear — reroute needed
        "ata_carnet_savings_usd": 35_000,
        "processing_hours_standard":  72,  # blocked
        "processing_hours_expedited": 6,   # if rerouted via Busan
        "notes": "Active regulatory hold blocks standard clearance. ATA carnet via Busan: $18K, 6h.",
    },
    ScenarioType.SUPPLIER_BREACH: {
        "standard_usd":          15_000,
        "expedited_usd":         32_000,
        "strike_surcharge_usd":  0,
        "processing_hours_standard":  4,
        "processing_hours_expedited": 1,
        "notes": "No port disruption. Standard customs applies.",
    },
}


# ── Pure-Python normal distribution (no numpy needed) ────────────────────
# Uses Box-Muller transform for hackathon portability.
# Phase 3 can swap in numpy if available.

def _normal_samples(mean: float, std: float, n: int) -> list[float]:
    samples = []
    for _ in range(n // 2 + 1):
        # Box-Muller
        u1 = random.random() or 1e-10
        u2 = random.random()
        z0 = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
        z1 = math.sqrt(-2 * math.log(u1)) * math.sin(2 * math.pi * u2)
        samples.append(mean + std * z0)
        samples.append(mean + std * z1)
    return samples[:n]


def _histogram(samples: list[float], bins: int = 22) -> tuple[list[int], list[float]]:
    lo, hi = min(samples), max(samples)
    width = (hi - lo) / bins if hi != lo else 1.0
    counts = [0] * bins
    for s in samples:
        idx = min(int((s - lo) / width), bins - 1)
        counts[idx] += 1
    edges = [lo + i * width for i in range(bins + 1)]
    return counts, edges


def _percentile(samples: list[float], p: float) -> float:
    sorted_s = sorted(samples)
    idx = (p / 100) * (len(sorted_s) - 1)
    lo_i, hi_i = int(idx), min(int(idx) + 1, len(sorted_s) - 1)
    return sorted_s[lo_i] + (idx - lo_i) * (sorted_s[hi_i] - sorted_s[lo_i])


# ── Tool functions ────────────────────────────────────────────────────────

async def run_monte_carlo(
    base_cost_usd: int,
    n_iterations: int = 100,
    std_fraction: float = 0.15,
) -> dict:
    """
    Monte Carlo simulation over cost uncertainty.

    Args:
        base_cost_usd:  Centre of the distribution (the recommended option cost)
        n_iterations:   Number of simulation runs (100 is visible + fast)
        std_fraction:   Standard deviation as fraction of base cost (0.15 = 15%)

    Returns:
        mean, p10, p90, confidence_interval, distribution (22 buckets for D3)
    """
    # Simulate compute time (makes it feel like real work)
    await asyncio.sleep(0.4)

    std = base_cost_usd * std_fraction
    samples = _normal_samples(float(base_cost_usd), std, n_iterations)

    # Clip at 0 — can't have negative costs
    samples = [max(0.0, s) for s in samples]

    counts, edges = _histogram(samples, bins=22)
    mean_val = sum(samples) / len(samples)
    p10 = _percentile(samples, 10)
    p90 = _percentile(samples, 90)

    # CI: proportion within ±1.5 std of mean
    within = sum(1 for s in samples if abs(s - mean_val) <= 1.5 * std)
    ci = round(within / len(samples), 2)

    return {
        "iterations":          n_iterations,
        "mean_usd":            int(mean_val),
        "p10_usd":             int(p10),
        "p90_usd":             int(p90),
        "std_usd":             int(std),
        "confidence_interval": ci,
        # 22-bucket histogram — sent directly to frontend D3 chart
        "distribution":        counts,
        "bucket_edges_usd":    [int(e) for e in edges],
    }


async def query_customs_rates(scenario: ScenarioType) -> dict:
    """
    Returns customs clearance rates for the scenario.
    Finance agent uses this to challenge the Logistics cost estimate.
    Simulates 200ms lookup.
    """
    await asyncio.sleep(0.2)
    return _CUSTOMS_RATES.get(scenario, _CUSTOMS_RATES[ScenarioType.PORT_STRIKE])
