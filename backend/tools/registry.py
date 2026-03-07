"""
tools/registry.py
─────────────────
Phase 3 — Tool result formatter.

Every tool call produces a raw dict result.  This module wraps that into a
`display` shape that the frontend renders as a rich bubble in the chat log.

The display shape is keyed by `kind`:

  "freight"     — route comparison table (3 options, cost / hours / risk)
  "memory"      — episodic memory card   (date, decision, savings, confidence)
  "monte_carlo" — MC summary card        (mean, p10, p90, CI, distribution)
  "customs"     — customs rate table     (standard / expedited / surcharge)
  "supplier"    — supplier option table  (name, qty%, cost, transit, cert)
  "contract"    — contract terms card    (customer, penalty, extension, status)
  "amendment"   — SLA amendment card     (id, granted hours, penalty waived)
  "recalculate" — route revision card    (original, adjustment, revised cost)
  "table"       — generic key-value table (fallback for any unknown tool)

All formatters return a plain dict so it can be JSON-serialised directly.
Nothing here touches the database or any async I/O — pure transformation.
"""

from __future__ import annotations


# ── Public entry point ────────────────────────────────────────────────────

def format_tool_result(tool_name: str, raw: dict | list | None) -> dict:
    """
    Route a raw tool result to the correct formatter.
    Always returns a valid display dict — never raises.
    """
    if raw is None:
        return _generic_table(tool_name, {})

    formatters = {
        "check_freight_rates":  _fmt_freight,
        "memory_recall":        _fmt_memory,
        "recalculate_route":    _fmt_recalculate,
        "run_monte_carlo":      _fmt_monte_carlo,
        "query_customs_rates":  _fmt_customs,
        "query_suppliers":      _fmt_suppliers,
        "query_contract_terms": _fmt_contract,
        "draft_sla_amendment":  _fmt_amendment,
    }
    fn = formatters.get(tool_name)
    if fn:
        try:
            return fn(raw)
        except Exception as exc:
            # Never break the run because of a formatting bug
            return _generic_table(tool_name, {"error": str(exc), "raw": str(raw)[:200]})

    return _generic_table(tool_name, raw if isinstance(raw, dict) else {"result": str(raw)})


# ── Individual formatters ─────────────────────────────────────────────────

def _fmt_freight(raw: dict) -> dict:
    """
    3-option route comparison table.
    Each column: option key, carrier, cost, hours, risk, notes.
    """
    rows = []
    for key, opt in raw.items():
        carrier = opt.get("carrier", "—")
        cost    = f"${opt.get('cost_usd', 0) // 1_000:,}K"
        hours   = f"{opt.get('transit_hours', '?')}h"
        risk    = opt.get("risk_level", "?").upper()
        cap     = f"{opt.get('capacity_pct', '?')}% capacity"
        notes   = opt.get("notes", "")

        risk_emoji = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}.get(risk, "⚪")
        rows.append([
            key.replace("_", " ").upper(),
            carrier,
            cost,
            hours,
            f"{risk_emoji} {risk}",
            cap,
            notes,
        ])

    return {
        "kind":    "freight",
        "title":   "📦 check_freight_rates() — Live Results",
        "headers": ["Option", "Carrier", "Cost", "Transit", "Risk", "Capacity", "Notes"],
        "rows":    rows,
        "badge":   None,
    }


def _fmt_memory(raw: dict) -> dict:
    """
    Episodic memory card — the 📚 memory badge moment.
    Shows date, crisis, decision, outcome, savings, confidence.
    """
    if not raw:
        return _generic_table("memory_recall", {"result": "No matching memory found."})

    conf     = raw.get("confidence", 0)
    conf_pct = f"{int(conf * 100)}%"
    saved    = raw.get("saved_usd", 0)
    cost     = raw.get("cost_usd", 0)

    return {
        "kind":       "memory",
        "title":      f"📚 memory_recall(\"{raw.get('memory_key', '?')}\") — Episodic Match",
        "date":       raw.get("date", "Unknown date"),
        "crisis":     raw.get("crisis", ""),
        "decision":   raw.get("decision", ""),
        "outcome":    raw.get("outcome", ""),
        "learning":   raw.get("key_learning", ""),
        "cost_usd":   f"${cost // 1_000:,}K",
        "saved_usd":  f"${saved // 1_000:,}K",
        "confidence": conf_pct,
        # Compact rows for table-style fallback in older frontends
        "rows": [
            ["Date",       raw.get("date", "?")],
            ["Crisis",     raw.get("crisis", "?")[:80]],
            ["Decision",   raw.get("decision", "?")[:80]],
            ["Outcome",    raw.get("outcome", "?")],
            ["Cost",       f"${cost // 1_000:,}K"],
            ["Saved",      f"${saved // 1_000:,}K"],
            ["Confidence", conf_pct],
        ],
        "badge": {
            "label": f"📚 {raw.get('date', '')} · Saved {f'${saved // 1_000:,}K'}",
            "color": "#00d4ff",
        },
    }


def _fmt_recalculate(raw: dict) -> dict:
    """Route revision card — shows the Finance challenge was absorbed."""
    orig  = raw.get("original_option", "?").replace("_", " ").upper()
    extra = raw.get("extra_cost_usd", 0)
    rev   = raw.get("revised_cost_usd", 0)
    rec   = raw.get("recommendation", "hybrid_60_40").replace("_", " ").upper()

    return {
        "kind":  "recalculate",
        "title": "📦 recalculate_route() — Revised Estimate",
        "rows": [
            ["Original option",   orig],
            ["Adjustment",        raw.get("adjustment", "customs surcharge")],
            ["Extra cost",        f"+${extra // 1_000:,}K"],
            ["Revised total",     f"${rev // 1_000:,}K"],
            ["Revised transit",   f"{raw.get('revised_hours', '?')}h"],
            ["Recommendation",    rec],
            ["Reason",            raw.get("reason", "")[:100]],
        ],
        "badge": {
            "label": f"✅ Pivoting to {rec}",
            "color": "#00e676",
        },
    }


def _fmt_monte_carlo(raw: dict) -> dict:
    """
    Monte Carlo summary card.
    Includes the 22-bucket distribution array so the frontend
    can immediately rebuild the D3 chart without a separate fetch.
    """
    mean = raw.get("mean_usd", 0)
    p10  = raw.get("p10_usd", 0)
    p90  = raw.get("p90_usd", 0)
    ci   = raw.get("confidence_interval", 0)
    n    = raw.get("iterations", 100)
    std  = raw.get("std_usd", 0)

    return {
        "kind":         "monte_carlo",
        "title":        f"📊 run_monte_carlo({n}) — Cost Distribution",
        "mean_usd":     f"${mean // 1_000:,}K",
        "p10_usd":      f"${p10 // 1_000:,}K",
        "p90_usd":      f"${p90 // 1_000:,}K",
        "std_usd":      f"±${std // 1_000:,}K",
        "ci_pct":       f"{int(ci * 100)}%",
        "iterations":   n,
        "distribution": raw.get("distribution", []),       # 22 buckets for D3
        "bucket_edges": raw.get("bucket_edges_usd", []),   # 23 edges
        "rows": [
            ["Iterations",         str(n)],
            ["Mean cost",          f"${mean // 1_000:,}K"],
            ["P10 (best case)",    f"${p10 // 1_000:,}K"],
            ["P90 (worst case)",   f"${p90 // 1_000:,}K"],
            ["Std deviation",      f"±${std // 1_000:,}K"],
            ["Confidence interval", f"{int(ci * 100)}%"],
        ],
        "badge": {
            "label": f"📊 Mean ${mean // 1_000:,}K · CI {int(ci * 100)}%",
            "color": "#00e676",
        },
    }


def _fmt_customs(raw: dict) -> dict:
    """Customs rate table — Finance uses this to challenge Logistics."""
    rows = []
    for k, v in raw.items():
        if k == "notes":
            continue
        label = k.replace("_", " ").replace("usd", "").strip().title()
        if isinstance(v, int):
            rows.append([label, f"${v // 1_000:,}K" if v >= 1_000 else f"${v:,}"])
        else:
            rows.append([label, str(v)])

    notes = raw.get("notes", "")
    if notes:
        rows.append(["Notes", notes])

    return {
        "kind":  "customs",
        "title": "💰 query_customs_rates() — Live Rates",
        "rows":  rows,
        "badge": {
            "label": f"💰 Surcharge: ${raw.get('expedited_strike_total_usd', raw.get('expedited_usd', 0)) // 1_000:,}K",
            "color": "#ff3b5c",
        },
    }


def _fmt_suppliers(raw: list | dict) -> dict:
    """Supplier option table."""
    items = raw if isinstance(raw, list) else [raw]
    rows = []
    for s in items:
        if not s.get("total_cost_usd"):
            continue
        rows.append([
            s.get("name", "?")[:35],
            s.get("location", "?"),
            f"{s.get('stock_quantity_pct', '?')}%",
            f"${s.get('total_cost_usd', 0) // 1_000:,}K",
            f"{s.get('transit_hours', '?')}h",
            f"{s.get('cert_hours', 0)}h cert",
            s.get("risk_level", "?").upper(),
        ])

    if not rows:
        rows = [["No viable suppliers found for this scenario.", "", "", "", "", "", ""]]

    return {
        "kind":    "supplier",
        "title":   "🏭 query_suppliers() — Available Options",
        "headers": ["Supplier", "Location", "Qty%", "Cost", "Transit", "Cert", "Risk"],
        "rows":    rows,
        "badge":   None,
    }


def _fmt_contract(raw: dict) -> dict:
    """Contract terms card."""
    penalty_waived = raw.get("penalty_waived", False)
    ext_accepted   = raw.get("extension_accepted", False)
    ext_hours      = raw.get("extension_hours", 0)

    status_label = "✅ Extension confirmed" if ext_accepted else "⚠️ Extension pending"
    penalty_label = "✅ Waived" if penalty_waived else "❌ At risk"

    return {
        "kind":  "contract",
        "title": f"📋 query_contract_terms() — {raw.get('customer', 'Customer')}",
        "rows": [
            ["Customer",      raw.get("customer", "?")],
            ["Contract ref",  raw.get("contract_ref", "?")],
            ["SLA deadline",  f"{raw.get('sla_delivery_hours', '?')}h"],
            ["Penalty clause", raw.get("penalty_clause", "?")[:80]],
            ["Extension",     f"{ext_hours}h granted — {status_label}"],
            ["Penalty",       penalty_label],
            ["Q3 benefit",    raw.get("q3_priority_benefit", "N/A") or "N/A"],
            ["Notes",         (raw.get("notes", "") or "")[:100]],
        ],
        "badge": {
            "label": f"{'✅' if penalty_waived else '⚠️'} Penalty {penalty_label} · +{ext_hours}h extension",
            "color": "#00e676" if penalty_waived else "#ffb340",
        },
    }


def _fmt_amendment(raw: dict) -> dict:
    """SLA amendment confirmation card."""
    return {
        "kind":  "amendment",
        "title": "📝 draft_sla_amendment() — Amendment Confirmed",
        "rows": [
            ["Amendment ID",    raw.get("amendment_id", "?")],
            ["Customer",        raw.get("customer", "?")],
            ["Extension granted", f"{raw.get('extension_granted', 0)}h"],
            ["New delivery plan", raw.get("new_plan", "?")[:80]],
            ["Penalty waived",  "✅ Yes" if raw.get("penalty_waived") else "❌ No"],
            ["Status",          raw.get("status", "?").replace("_", " ").title()],
            ["Next step",       raw.get("next_step", "")[:80]],
        ],
        "badge": {
            "label": f"📝 Amendment {raw.get('amendment_id', '?')} · Penalty {'Waived' if raw.get('penalty_waived') else 'At Risk'}",
            "color": "#00e676" if raw.get("penalty_waived") else "#ffb340",
        },
    }


def _generic_table(tool_name: str, raw: dict) -> dict:
    """Fallback: render any dict as a simple key-value table."""
    rows = [[k.replace("_", " ").title(), str(v)[:120]]
            for k, v in raw.items() if v is not None]
    if not rows:
        rows = [["Result", "No data returned."]]
    return {
        "kind":  "table",
        "title": f"⚙ {tool_name}() — Output",
        "rows":  rows,
        "badge": None,
    }
