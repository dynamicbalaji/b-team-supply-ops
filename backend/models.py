"""
models.py
─────────
All Pydantic models for request bodies, response shapes, and SSE event payloads.
Keeping them in one file makes the SSE contract easy to cross-reference
when wiring the frontend.
"""

from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field
from enum import Enum
import uuid


# ── Enums ────────────────────────────────────────────────────────────────

class ScenarioType(str, Enum):
    PORT_STRIKE     = "port_strike"
    CUSTOMS_DELAY   = "customs_delay"
    SUPPLIER_BREACH = "supplier_breach"


class RunStatus(str, Enum):
    PENDING    = "pending"
    RUNNING    = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED   = "approved"
    COMPLETE   = "complete"
    FAILED     = "failed"


class AgentId(str, Enum):
    ORCHESTRATOR = "orchestrator"
    LOGISTICS    = "logistics"
    FINANCE      = "finance"
    PROCUREMENT  = "procurement"
    SALES        = "sales"
    RISK         = "risk"


class AgentStatus(str, Enum):
    STANDBY     = "STANDBY"
    ACTIVATING  = "ACTIVATING"
    PROPOSING   = "PROPOSING"
    QUERYING    = "QUERYING"
    CALCULATING = "CALCULATING"
    REVISING    = "REVISING"
    NEGOTIATING = "NEGOTIATING"
    CONSENSUS   = "CONSENSUS"
    FINALISING  = "FINALISING"
    DONE        = "DONE"
    COMPLETE    = "COMPLETE"


# ── Request bodies ───────────────────────────────────────────────────────

class CreateRunRequest(BaseModel):
    scenario: ScenarioType = ScenarioType.PORT_STRIKE


class ApproveRunRequest(BaseModel):
    approved: bool = True
    notes: str = ""


# ── Scenario definitions (returned by GET /api/scenarios) ───────────────

class ScenarioDefinition(BaseModel):
    id: ScenarioType
    name: str
    description: str
    crisis_title: str
    crisis_detail: str
    penalty_usd: int
    deadline_hours: int
    budget_cap_usd: int
    shipment_value_usd: int
    customer: str


# ── Run response ─────────────────────────────────────────────────────────

class RunResponse(BaseModel):
    run_id: str
    scenario: ScenarioType
    status: RunStatus
    stream_url: str          # convenience — frontend opens EventSource here
    approve_url: str


# ── SSE Event payloads ────────────────────────────────────────────────────
# These are the exact JSON shapes the frontend handleEvent() function reads.
# Every event has a "type" discriminator field.

class PhaseEvent(BaseModel):
    type: Literal["phase"] = "phase"
    phase: int               # 0–4
    status: Literal["active", "done"]

class AgentStateEvent(BaseModel):
    type: Literal["agent_state"] = "agent_state"
    agent: AgentId
    status: AgentStatus
    tool: str = ""           # tool pill text e.g. "📦 check_freight_rates()"
    confidence: float | None = None   # 0.0–1.0
    pulsing: bool = True

class MessageEvent(BaseModel):
    type: Literal["message"] = "message"
    agent: AgentId
    from_label: str          # display label e.g. "LOGISTICS"
    to_label: str            # e.g. "→ FINANCE"
    timestamp: str           # display string e.g. "01:04"
    css_class: str           # al | af | ap | as_ | ar | orc
    text: str                # HTML allowed (same as wireframe)
    tools: list[str] = []    # tool pill labels

class TokenEvent(BaseModel):
    """Streaming token — Phase 2 only. Not used in Phase 1."""
    type: Literal["token"] = "token"
    agent: AgentId
    content: str

class ToolEvent(BaseModel):
    type: Literal["tool"] = "tool"
    agent: AgentId
    tool: str
    result: Any = None


class ToolResultEvent(BaseModel):
    """
    Phase 3: rich tool-result bubble rendered directly in the chat log.

    display.kind controls how the frontend renders it:
      "table"       -- rows: [[label, value], ...] + optional badge
      "memory"      -- episodic memory card (date / decision / savings)
      "monte_carlo" -- inline histogram summary (mean / p10 / p90 + distribution)
      "freight"     -- route comparison table
    """
    type: Literal["tool_result"] = "tool_result"
    agent: AgentId
    tool: str                # function name, e.g. "check_freight_rates"
    display: dict            # {kind, title, rows?, badge?, ...}
    # raw result still attached so existing handleTool() logic keeps working
    result: Any = None

class RiskActivatedEvent(BaseModel):
    type: Literal["risk_activated"] = "risk_activated"
    message: str

class ApprovalRequiredEvent(BaseModel):
    type: Literal["approval_required"] = "approval_required"
    option: str              # "hybrid"
    label: str               # "Hybrid Route — 60% Air / 40% Sea"
    cost_usd: int
    reserve_usd: int
    delivery_hours: int
    confidence: float
    detail: str

class MapUpdateEvent(BaseModel):
    type: Literal["map_update"] = "map_update"
    status: str
    status_color: str        # hex e.g. "#ffb340"
    route: str | None = None

class ExecutionEvent(BaseModel):
    type: Literal["execution"] = "execution"
    agent: AgentId
    from_label: str
    css_class: str
    timestamp: str
    text: str

class CompleteEvent(BaseModel):
    type: Literal["complete"] = "complete"
    resolution_time: str     # "4m 32s"
    cost_usd: int
    saved_usd: int
    message_count: int

class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    message: str

class PingEvent(BaseModel):
    type: Literal["ping"] = "ping"


# ── Health check ─────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    redis: bool
    env: str
