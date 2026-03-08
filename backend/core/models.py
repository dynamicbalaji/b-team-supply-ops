"""
models.py
─────────
All Pydantic models for request bodies, response shapes, and SSE event payloads.
Keeping them in one file makes the SSE contract easy to cross-reference
when wiring the frontend.
"""

from __future__ import annotations
from typing import Any, Literal, Optional
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

class AuditEvent(BaseModel):
    """
    Emitted by each LangGraph node after a significant decision step.
    Accumulated in orchestrator._runs[run_id]["audit_trail"] and streamed
    via SSE so AuditTab can build a live timeline without hardcoded data.

    Call audit_helpers.publish_audit_event() inside each agent graph node
    to emit these. The REST endpoint GET /api/runs/{id}/audit-trail reads
    the accumulated audit_trail list from the in-memory run registry.
    """
    type:        Literal["audit"] = "audit"
    time_label:  str              # "00:12 — Route Options"
    agent_color: str              # "#00d4ff"
    agent_label: str              # "🔵 Logistics Agent"
    description: str
    data:        str            = ""
    memory_note: Optional[str] = None
    elapsed_s:   int           = 0


# ── A2A Task models (§4.1 A2A Protocol Specification v0.3.0) ─────────────
#
# A2ATaskRequest  — body for POST /agents/{name}/tasks
# A2ATaskResult   — response from that endpoint
#
# Field mapping to the A2A spec:
#   task            ≈  skill id from the agent's AgentCard
#   inputs          ≈  message parts (structured JSON rather than free text)
#   conversation_id ≈  contextId  — groups multi-turn interactions
#   metadata        ≈  SendMessageConfiguration.metadata
#
#   status          ≈  TaskState  (submitted/working/completed/failed)
#   task_id         ≈  Task.id
#   outputs         ≈  Task artifacts (structured agent answer)
#   messages        ≈  Message list (agent's natural-language explanation)
#   error           ≈  TaskStatus.message when state=failed

class A2ATaskRequest(BaseModel):
    """
    Request body for POST /agents/{agent_name}/tasks.

    task            : Skill id to invoke (e.g. "check_freight", "run_monte_carlo").
                      Falls back to the agent's default skill if omitted or unknown.
    inputs          : Arbitrary JSON passed to the skill.  Common keys:
                        scenario         — "port_strike" | "customs_delay" | "supplier_breach"
                        base_cost_usd    — override base cost for Monte Carlo
                        hybrid_cost_usd  — upstream logistics cost for finance / risk
                        challenge        — Finance challenge text for logistics revise_route
                        customs_surcharge— int USD for logistics revise_route
                        reserve_usd      — contingency reserve for finance propose_consensus
                        query            — free-text for logistics recall_memory
                        location_hint    — location string for procurement query_suppliers
                        logistics        — full logistics output dict (upstream context)
                        finance          — full finance output dict (upstream context)
    conversation_id : Optional contextId grouping multi-turn calls (stored in metadata).
    metadata        : Arbitrary caller metadata (forwarded into task result unchanged).
    """
    task:            str            = "evaluate_crisis"
    inputs:          dict[str, Any] = Field(default_factory=dict)
    conversation_id: Optional[str]  = None
    metadata:        Optional[dict[str, Any]] = None


class A2ATaskResult(BaseModel):
    """
    Response shape for POST /agents/{agent_name}/tasks.

    status    : "completed" | "failed"  (A2A TaskState values)
    task_id   : UUID identifying this invocation (use in GET /api/stream/{task_id}
                to receive SSE token events if the client wants streaming).
    agent     : Which agent handled the task.
    task      : The resolved skill name that was executed.
    outputs   : Structured agent answer (agent-specific schema, see AgentCard skills).
    messages  : Natural-language explanation from the agent (one string per turn).
    error     : Non-null only when status="failed".
    metadata  : Echo of caller metadata + internal timing/scenario fields.
    """
    status:   Literal["completed", "failed"]
    task_id:  str
    agent:    str
    task:     str
    outputs:  dict[str, Any]         = Field(default_factory=dict)
    messages: list[str]              = Field(default_factory=list)
    error:    Optional[str]          = None
    metadata: dict[str, Any]         = Field(default_factory=dict)


# ── Health check ─────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    redis: bool
    env: str
