"""
turso_client.py
───────────────
TursoDB (libSQL) persistence layer for ResolveIQ.

Replaces all in-memory dicts that were Phase 2 stubs:
  • _runs   (orchestrator.py)  → table: runs
  • _MEMORY_BANK (freight.py)  → table: episodic_memory
  • _SUPPLIERS (suppliers.py)  → table: suppliers  [seeded at startup]
  • _CONTRACT_TERMS (suppliers.py) → table: contracts [seeded at startup]

The module is import-safe: if TURSO_DATABASE_URL is empty or the SDK is
not installed, every public function degrades to a no-op / None / empty
list so the in-memory fallbacks in tools/*.py continue to work.

Install:
    pip install libsql-client

Turso setup (free tier):
    turso db create resolveiq
    turso db tokens create resolveiq
    # Copy the URL and token into .env as TURSO_DATABASE_URL / TURSO_AUTH_TOKEN

4-table schema (created automatically on first startup):
    runs              — one row per scenario run (replaces orchestrator._runs)
    episodic_memory   — historical crises recalled by memory_recall()
    suppliers         — alternative supplier catalog per scenario
    contracts         — customer SLA terms per scenario
"""

from __future__ import annotations

import json
import logging
import asyncio
from typing import Any

from config import get_settings

log = logging.getLogger("resolveiq.turso")

# ── Optional SDK import ────────────────────────────────────────────────────

try:
    import libsql_client as libsql          # pip install libsql-client
    _SDK_AVAILABLE = True
except ImportError:
    libsql = None                           # type: ignore
    _SDK_AVAILABLE = False


# ── Connection factory ─────────────────────────────────────────────────────

def _get_client():
    """
    Returns a new async libsql client or None if not configured.
    Callers must use `async with _get_client() as c:`.
    """
    if not _SDK_AVAILABLE:
        return None
    cfg = get_settings()
    if not cfg.turso_database_url or not cfg.turso_auth_token:
        return None
    try:
        return libsql.create_client(
            url=cfg.turso_database_url,
            auth_token=cfg.turso_auth_token,
            # Use sync_interval=0 to avoid persistent background connections
            # which can cause issues with WebSocket handshakes during startup
        )
    except Exception as e:
        log.warning("Failed to create Turso client: %s", e)
        return None


def is_configured() -> bool:
    cfg = get_settings()
    url = cfg.turso_database_url
    token = cfg.turso_auth_token
    
    is_valid = (
        _SDK_AVAILABLE
        and bool(url)
        and bool(token)
        and url != "libsql://your-db-name.turso.io"
        and token != "your_auth_token_here"
    )
    
    if is_valid and not url.startswith(("libsql://", "wss://", "https://")):
        log.warning("Invalid Turso URL scheme: %s (should start with libsql://, wss://, or https://)", url[:20])
        return False
    
    return is_valid


def _validate_config() -> tuple[bool, str]:
    """
    Validates Turso configuration and returns (is_valid, error_message).
    Checks for common configuration mistakes.
    """
    cfg = get_settings()
    url = cfg.turso_database_url
    token = cfg.turso_auth_token
    
    if not url or not token:
        return False, "TURSO_DATABASE_URL and TURSO_AUTH_TOKEN not set in .env"
    
    if url == "libsql://your-db-name.turso.io":
        return False, "TURSO_DATABASE_URL still has placeholder value"
    
    if token == "your_auth_token_here":
        return False, "TURSO_AUTH_TOKEN still has placeholder value"
    
    if not url.startswith(("libsql://", "wss://", "https://")):
        return False, f"Invalid TURSO_DATABASE_URL scheme: {url[:30]}... (must start with libsql://)"
    
    if len(token) < 20:
        return False, "TURSO_AUTH_TOKEN appears too short (likely invalid)"
    
    log.debug("Config validation passed | URL=%s | Token length=%d", url[:50], len(token))
    return True, ""


# ── Schema ─────────────────────────────────────────────────────────────────

_SCHEMA_SQL = [
    # ── runs ──────────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS runs (
        run_id      TEXT PRIMARY KEY,
        scenario    TEXT NOT NULL,
        status      TEXT NOT NULL DEFAULT 'pending',
        mode        TEXT NOT NULL DEFAULT 'live',
        approved    INTEGER NOT NULL DEFAULT 0,
        context_json TEXT,
        created_at  TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    # ── episodic_memory ───────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS episodic_memory (
        memory_key      TEXT PRIMARY KEY,
        scenario_type   TEXT NOT NULL,
        date_label      TEXT NOT NULL,
        crisis          TEXT NOT NULL,
        decision        TEXT NOT NULL,
        outcome         TEXT NOT NULL,
        cost_usd        INTEGER NOT NULL DEFAULT 0,
        saved_usd       INTEGER NOT NULL DEFAULT 0,
        key_learning    TEXT NOT NULL DEFAULT '',
        confidence      REAL  NOT NULL DEFAULT 0.9
    )
    """,
    # ── suppliers ─────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS suppliers (
        id                     TEXT PRIMARY KEY,
        scenario_type          TEXT NOT NULL,
        name                   TEXT NOT NULL,
        location               TEXT NOT NULL,
        distance_from_la       TEXT NOT NULL DEFAULT '',
        stock_quantity_pct     INTEGER NOT NULL DEFAULT 0,
        unit_cost_premium_pct  INTEGER NOT NULL DEFAULT 0,
        total_cost_usd         INTEGER NOT NULL DEFAULT 0,
        transit_hours          INTEGER NOT NULL DEFAULT 24,
        cert_hours             INTEGER NOT NULL DEFAULT 0,
        risk_level             TEXT NOT NULL DEFAULT 'medium',
        notes                  TEXT NOT NULL DEFAULT '',
        contact                TEXT NOT NULL DEFAULT ''
    )
    """,
    # ── contracts ─────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS contracts (
        scenario_type          TEXT PRIMARY KEY,
        customer               TEXT NOT NULL,
        contract_ref           TEXT NOT NULL,
        penalty_clause         TEXT NOT NULL,
        sla_delivery_hours     INTEGER NOT NULL,
        current_delay_risk_h   INTEGER NOT NULL DEFAULT 0,
        extension_terms        TEXT NOT NULL DEFAULT '',
        extension_accepted     INTEGER NOT NULL DEFAULT 1,
        extension_hours        INTEGER NOT NULL DEFAULT 0,
        q3_priority_available  INTEGER NOT NULL DEFAULT 0,
        q3_priority_benefit    TEXT NOT NULL DEFAULT '',
        penalty_waived         INTEGER NOT NULL DEFAULT 1,
        amendment_ref          TEXT,
        customer_contact       TEXT NOT NULL DEFAULT '',
        notes                  TEXT NOT NULL DEFAULT ''
    )
    """,
]

# ── Seed data (mirrors the in-memory dicts exactly) ────────────────────────

_SEED_MEMORY = [
    {
        "memory_key": "LA_port_strike",
        "scenario_type": "port_strike",
        "date_label": "March 2024",
        "crisis": "ILWU walkout — Long Beach + LA ports closed 11 days",
        "decision": "Hybrid 60/40 air/sea split via LAX + Oakland",
        "outcome": "Delivered within 38h. Zero penalty.",
        "cost_usd": 272_000,
        "saved_usd": 180_000,
        "key_learning": "Air-only was at budget cap due to strike customs surcharge. Hybrid beat it by $178K.",
        "confidence": 0.94,
    },
    {
        "memory_key": "Shanghai_customs_2023",
        "scenario_type": "customs_delay",
        "date_label": "September 2023",
        "crisis": "SAMR hold on semiconductor exports — 72h freeze",
        "decision": "Reroute via Busan + ATA carnet pre-clearance at LAX",
        "outcome": "Cleared in 29h. $1.2M penalty avoided.",
        "cost_usd": 198_000,
        "saved_usd": 145_000,
        "key_learning": "ATA carnet pre-clearance added 6h but saved 40h of customs processing.",
        "confidence": 0.89,
    },
    {
        "memory_key": "Taiwan_drought_2022",
        "scenario_type": "supplier_breach",
        "date_label": "July 2022",
        "crisis": "TSMC production halt — water rationing reduced fab output 35%",
        "decision": "Dual-source Samsung Suwon + MediaTek Thailand for 60-day bridge",
        "outcome": "Zero stockout. Production maintained.",
        "cost_usd": 520_000,
        "saved_usd": 420_000,
        "key_learning": "Alt-sourcing qualification ran parallel to negotiation — saved 2 weeks.",
        "confidence": 0.87,
    },
]

_SEED_SUPPLIERS = [
    # port_strike
    {"id": "SUP-TX-001", "scenario_type": "port_strike", "name": "Texas Semiconductor Warehouse",
     "location": "Dallas, TX", "distance_from_la": "1,432 miles", "stock_quantity_pct": 80,
     "unit_cost_premium_pct": 12, "total_cost_usd": 380_000, "transit_hours": 12, "cert_hours": 4,
     "risk_level": "medium", "notes": "80% of order quantity in stock. Remaining 20% needs 4h certification.",
     "contact": "ops@texsemi.example.com"},
    {"id": "SUP-AZ-002", "scenario_type": "port_strike", "name": "Tucson Air Logistics Hub",
     "location": "Tucson, AZ", "distance_from_la": "494 miles", "stock_quantity_pct": 0,
     "unit_cost_premium_pct": 0, "total_cost_usd": 0, "transit_hours": 8, "cert_hours": 0,
     "risk_level": "low", "notes": "Backup air routing hub. Not a supplier — used for Hour-20 contingency trigger.",
     "contact": "ops@tucsonair.example.com"},
    # customs_delay
    {"id": "SUP-KR-001", "scenario_type": "customs_delay", "name": "Samsung Suwon Component Hub",
     "location": "Suwon, South Korea", "distance_from_la": "5,800 miles", "stock_quantity_pct": 100,
     "unit_cost_premium_pct": 8, "total_cost_usd": 265_000, "transit_hours": 22, "cert_hours": 2,
     "risk_level": "low", "notes": "Full quantity available. Spec-equivalent confirmed. Customs pre-cleared via Busan.",
     "contact": "logistics@samsungsupply.example.com"},
    # supplier_breach
    {"id": "SUP-KR-002", "scenario_type": "supplier_breach", "name": "SK Hynix Emergency Supply",
     "location": "Icheon, South Korea", "distance_from_la": "5,750 miles", "stock_quantity_pct": 65,
     "unit_cost_premium_pct": 18, "total_cost_usd": 510_000, "transit_hours": 20, "cert_hours": 6,
     "risk_level": "medium", "notes": "65% of NVIDIA spec available immediately. Balance in 72h.",
     "contact": "supply@skhynix.example.com"},
    {"id": "SUP-JP-001", "scenario_type": "supplier_breach", "name": "Micron Japan Fab Bridge",
     "location": "Hiroshima, Japan", "distance_from_la": "5,450 miles", "stock_quantity_pct": 45,
     "unit_cost_premium_pct": 22, "total_cost_usd": 390_000, "transit_hours": 18, "cert_hours": 8,
     "risk_level": "medium", "notes": "45% available. 8h cert due to wafer process difference.",
     "contact": "emergency@micron-jp.example.com"},
]

_SEED_CONTRACTS = [
    {"scenario_type": "port_strike", "customer": "Apple Inc.", "contract_ref": "AAPL-SC-2024-Q3",
     "penalty_clause": "$2M USD per 48h breach of SLA delivery window",
     "sla_delivery_hours": 48, "current_delay_risk_h": 48,
     "extension_terms": "Customer may grant up to 72h extension at discretion with written notice",
     "extension_accepted": 1, "extension_hours": 36,
     "q3_priority_available": 1, "q3_priority_benefit": "Q3 allocation bumped to Tier 1 — guaranteed slot in next 3 production cycles",
     "penalty_waived": 1, "amendment_ref": "AAPL-AMD-2024-0312",
     "customer_contact": "Apple Supply Chain Operations, Cupertino CA",
     "notes": "Apple has confirmed 36h extension verbally — amendment pending legal review."},
    {"scenario_type": "customs_delay", "customer": "Samsung Electronics", "contract_ref": "SMSG-SC-2024-Q2",
     "penalty_clause": "$1.5M USD per 36h breach + production line halt compensation",
     "sla_delivery_hours": 36, "current_delay_risk_h": 36,
     "extension_terms": "Force majeure clause applicable for regulatory holds beyond 48h",
     "extension_accepted": 1, "extension_hours": 24,
     "q3_priority_available": 0, "q3_priority_benefit": "",
     "penalty_waived": 1, "amendment_ref": "SMSG-FM-2024-0891",
     "customer_contact": "Samsung Global Procurement, Seoul KR",
     "notes": "Force majeure invoked. Samsung waiving penalty. Requesting ETA update by EOD."},
    {"scenario_type": "supplier_breach", "customer": "NVIDIA", "contract_ref": "NVDA-SC-2024-Q3",
     "penalty_clause": "$5M USD + 15% of contract value for unilateral breach",
     "sla_delivery_hours": 72, "current_delay_risk_h": 90,
     "extension_terms": "NVIDIA has approval rights on any supplier substitution",
     "extension_accepted": 0, "extension_hours": 0,
     "q3_priority_available": 1, "q3_priority_benefit": "NVIDIA willing to accept alt-source if spec certified by their team",
     "penalty_waived": 0, "amendment_ref": None,
     "customer_contact": "NVIDIA Supply Chain Crisis Desk, Santa Clara CA",
     "notes": "NVIDIA requires spec certification before accepting substitution. 6h cert window offered."},
]


# ── Schema init (called from main.py lifespan) ─────────────────────────────

async def init_schema() -> bool:
    """
    Verify TursoDB connection and that required tables exist.
    Does NOT create tables or seed data (assumes they exist already).
    Returns True on success, False if TursoDB is not configured or connection fails.
    """
    # Pre-flight validation
    is_valid, error_msg = _validate_config()
    if not is_valid:
        log.warning("TursoDB configuration invalid: %s — skipping connection check (in-memory fallbacks active)", error_msg)
        return False

    if not is_configured():
        log.warning("TursoDB not configured — skipping connection check (in-memory fallbacks active)")
        return False

    client = _get_client()
    if client is None:
        log.warning("TursoDB client creation failed — skipping connection check (in-memory fallbacks active)")
        return False

    log.info("TursoDB: verifying connection and schema…")
    
    # Retry logic with exponential backoff
    max_retries = 3
    required_tables = ["runs", "episodic_memory", "suppliers", "contracts"]
    
    for attempt in range(max_retries):
        try:
            async with client as c:
                # Verify each required table exists with a simple query
                for table in required_tables:
                    rs = await c.execute(f"SELECT COUNT(*) FROM {table}")
                    row_count = rs.rows[0][0] if rs.rows else 0
                    log.debug(f"✓ Table '{table}' exists ({row_count} rows)")

            log.info("TursoDB: ✅ connection verified — all 4 required tables found and accessible")
            return True

        except (asyncio.TimeoutError, ConnectionError) as exc:
            wait_time = (2 ** attempt) + 1  # 2s, 3s, 5s (added base to avoid too-short waits)
            if attempt < max_retries - 1:
                log.warning("TursoDB connection attempt %d failed (%s), retrying in %ds…", 
                           attempt + 1, type(exc).__name__, wait_time)
                await asyncio.sleep(wait_time)
            else:
                log.error("TursoDB connection failed after %d attempts: %s — Verify: (1) database is running, (2) auth token hasn't expired, (3) network can reach wss://supportops-dynamicbalaji.aws-us-east-2.turso.io", 
                         max_retries, exc)
                return False
        except Exception as exc:
            exc_type = type(exc).__name__
            exc_msg = str(exc)
            
            # Provide helpful hints for common errors
            if "505" in exc_msg or "Invalid response status" in exc_msg:
                # 505 often means protocol issues with WebSocket handshake
                log.error("TursoDB WebSocket handshake failed (505): This may indicate:")
                log.error("  • The Turso server is temporarily unavailable")
                log.error("  • Network/firewall is blocking wss:// connections")
                log.error("  • Auth token is invalid or expired (run: turso db tokens create <db-name>)")
                log.error("  Full error: %s", exc_msg)
            elif "401" in exc_msg or "Unauthorized" in exc_msg:
                log.error("TursoDB auth failed (401): check that TURSO_AUTH_TOKEN is valid and not expired", exc_msg)
            elif "no such table" in exc_msg.lower():
                log.error("TursoDB schema mismatch: %s — required tables (%s) not found.", exc_msg, ", ".join(required_tables))
            else:
                log.error("TursoDB connection check failed (%s): %s", exc_type, exc_msg)
            return False
    
    return False

async def health_check() -> bool:
    """Ping TursoDB. Returns True if reachable."""
    if not is_configured():
        return False
    try:
        client = _get_client()
        if client is None:
            return False
        async with client as c:
            rs = await c.execute("SELECT 1")
            return len(rs.rows) > 0
    except asyncio.TimeoutError:
        log.warning("TursoDB health check timed out")
        return False
    except Exception as e:
        log.debug("TursoDB health check failed: %s", e)
        return False


# ── runs table ─────────────────────────────────────────────────────────────

async def create_run(run_id: str, scenario: str, mode: str = "live") -> bool:
    """Insert a new run row. Returns True on success."""
    client = _get_client()
    if client is None:
        return False
    try:
        async with client as c:
            await c.execute(
                """INSERT INTO runs (run_id, scenario, status, mode)
                   VALUES (?, ?, 'pending', ?)""",
                [run_id, scenario, mode],
            )
        return True
    except Exception as exc:
        log.error("TursoDB create_run failed: %s", exc)
        return False


async def get_run(run_id: str) -> dict | None:
    """Fetch a run by ID. Returns dict or None."""
    client = _get_client()
    if client is None:
        return None
    try:
        async with client as c:
            rs = await c.execute(
                "SELECT run_id, scenario, status, mode, approved, context_json, created_at, updated_at FROM runs WHERE run_id = ?",
                [run_id],
            )
            if not rs.rows:
                return None
            r = rs.rows[0]
            row = {
                "run_id":       r[0],
                "scenario":     r[1],
                "status":       r[2],
                "mode":         r[3],
                "approved":     bool(r[4]),
                "context_json": r[5],
                "created_at":   r[6],
                "updated_at":   r[7],
            }
            if row["context_json"]:
                row["context"] = json.loads(row["context_json"])
            return row
    except Exception as exc:
        log.error("TursoDB get_run failed: %s", exc)
        return None


async def update_run_status(run_id: str, status: str) -> bool:
    """Update run status + updated_at timestamp."""
    client = _get_client()
    if client is None:
        return False
    try:
        async with client as c:
            await c.execute(
                "UPDATE runs SET status = ?, updated_at = datetime('now') WHERE run_id = ?",
                [status, run_id],
            )
        return True
    except Exception as exc:
        log.error("TursoDB update_run_status failed: %s", exc)
        return False


async def save_run_context(run_id: str, context: dict) -> bool:
    """Persist the full run_context dict for post-run analysis."""
    client = _get_client()
    if client is None:
        return False
    try:
        safe = {
            agent: {k: v for k, v in data.items()
                    if isinstance(v, (str, int, float, bool, list, dict, type(None)))}
            for agent, data in context.items() if isinstance(data, dict)
        }
        async with client as c:
            await c.execute(
                "UPDATE runs SET context_json = ?, updated_at = datetime('now') WHERE run_id = ?",
                [json.dumps(safe), run_id],
            )
        return True
    except Exception as exc:
        log.error("TursoDB save_run_context failed: %s", exc)
        return False


async def list_recent_runs(limit: int = 20) -> list[dict]:
    """Return the N most recent runs for the /api/runs history endpoint."""
    client = _get_client()
    if client is None:
        return []
    try:
        async with client as c:
            rs = await c.execute(
                "SELECT run_id, scenario, status, mode, created_at FROM runs ORDER BY created_at DESC LIMIT ?",
                [limit],
            )
            return [
                {"run_id": r[0], "scenario": r[1], "status": r[2],
                 "mode": r[3], "created_at": r[4]}
                for r in rs.rows
            ]
    except Exception as exc:
        log.error("TursoDB list_recent_runs failed: %s", exc)
        return []


# ── episodic_memory table ──────────────────────────────────────────────────

async def recall_memory(query_keywords: list[str], scenario_type: str) -> dict | None:
    """
    Fuzzy memory lookup: tries keywords first, falls back to scenario_type match.
    Returns the best matching memory dict or None.
    """
    client = _get_client()
    if client is None:
        return None
    try:
        async with client as c:
            # 1. Keyword match on memory_key or crisis text
            for kw in query_keywords:
                rs = await c.execute(
                    """SELECT memory_key, scenario_type, date_label, crisis, decision,
                              outcome, cost_usd, saved_usd, key_learning, confidence
                       FROM episodic_memory
                       WHERE lower(memory_key) LIKE ? OR lower(crisis) LIKE ?
                       LIMIT 1""",
                    [f"%{kw.lower()}%", f"%{kw.lower()}%"],
                )
                if rs.rows:
                    return _memory_row_to_dict(rs.rows[0])

            # 2. Fallback: match by scenario type
            rs = await c.execute(
                """SELECT memory_key, scenario_type, date_label, crisis, decision,
                          outcome, cost_usd, saved_usd, key_learning, confidence
                   FROM episodic_memory WHERE scenario_type = ? LIMIT 1""",
                [scenario_type],
            )
            if rs.rows:
                return _memory_row_to_dict(rs.rows[0])
    except Exception as exc:
        log.error("TursoDB recall_memory failed: %s", exc)
    return None


def _memory_row_to_dict(r) -> dict:
    return {
        "memory_key":   r[0],
        "scenario_type": r[1],
        "date":         r[2],
        "crisis":       r[3],
        "decision":     r[4],
        "outcome":      r[5],
        "cost_usd":     r[6],
        "saved_usd":    r[7],
        "key_learning": r[8],
        "confidence":   r[9],
    }


async def save_memory(
    memory_key: str,
    scenario_type: str,
    date_label: str,
    crisis: str,
    decision: str,
    outcome: str,
    cost_usd: int,
    saved_usd: int,
    key_learning: str,
    confidence: float,
) -> bool:
    """
    Insert or replace a memory record.
    Called at end of each completed run to accumulate real operational history.
    """
    client = _get_client()
    if client is None:
        return False
    try:
        async with client as c:
            await c.execute(
                """INSERT OR REPLACE INTO episodic_memory
                   (memory_key, scenario_type, date_label, crisis, decision,
                    outcome, cost_usd, saved_usd, key_learning, confidence)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                [memory_key, scenario_type, date_label, crisis, decision,
                 outcome, cost_usd, saved_usd, key_learning, confidence],
            )
        return True
    except Exception as exc:
        log.error("TursoDB save_memory failed: %s", exc)
        return False


# ── suppliers table ────────────────────────────────────────────────────────

async def query_suppliers(scenario_type: str) -> list[dict]:
    """Return suppliers for a scenario, ordered by total_cost_usd."""
    client = _get_client()
    if client is None:
        return []
    try:
        async with client as c:
            rs = await c.execute(
                """SELECT id, scenario_type, name, location, distance_from_la,
                          stock_quantity_pct, unit_cost_premium_pct, total_cost_usd,
                          transit_hours, cert_hours, risk_level, notes, contact
                   FROM suppliers WHERE scenario_type = ?
                   ORDER BY total_cost_usd ASC""",
                [scenario_type],
            )
            return [_supplier_row_to_dict(r) for r in rs.rows]
    except Exception as exc:
        log.error("TursoDB query_suppliers failed: %s", exc)
        return []


def _supplier_row_to_dict(r) -> dict:
    return {
        "id": r[0], "scenario_type": r[1], "name": r[2], "location": r[3],
        "distance_from_la": r[4], "stock_quantity_pct": r[5],
        "unit_cost_premium_pct": r[6], "total_cost_usd": r[7],
        "transit_hours": r[8], "cert_hours": r[9],
        "risk_level": r[10], "notes": r[11], "contact": r[12],
    }


# ── contracts table ────────────────────────────────────────────────────────

async def query_contract(scenario_type: str) -> dict | None:
    """Return contract terms for a scenario."""
    client = _get_client()
    if client is None:
        return None
    try:
        async with client as c:
            rs = await c.execute(
                """SELECT scenario_type, customer, contract_ref, penalty_clause,
                          sla_delivery_hours, current_delay_risk_h, extension_terms,
                          extension_accepted, extension_hours, q3_priority_available,
                          q3_priority_benefit, penalty_waived, amendment_ref,
                          customer_contact, notes
                   FROM contracts WHERE scenario_type = ?""",
                [scenario_type],
            )
            if not rs.rows:
                return None
            r = rs.rows[0]
            return {
                "scenario_type":         r[0],
                "customer":              r[1],
                "contract_ref":          r[2],
                "penalty_clause":        r[3],
                "sla_delivery_hours":    r[4],
                "current_delay_risk_h":  r[5],
                "extension_terms":       r[6],
                "extension_accepted":    bool(r[7]),
                "extension_hours":       r[8],
                "q3_priority_available": bool(r[9]),
                "q3_priority_benefit":   r[10],
                "penalty_waived":        bool(r[11]),
                "amendment_ref":         r[12],
                "customer_contact":      r[13],
                "notes":                 r[14],
            }
    except Exception as exc:
        log.error("TursoDB query_contract failed: %s", exc)
        return None
