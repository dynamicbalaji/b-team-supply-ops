"""
graph/state.py
──────────────

Typed state used by LangGraph graphs in this backend.

This is intentionally minimal for the first migration phase. It captures
the core identifiers and high-level run metadata; later phases can
extend this with richer per-agent fields as we move more behaviour into
LangGraph.
"""

from __future__ import annotations

from typing import Any, Dict, TypedDict

from models import RunStatus, ScenarioType


class RunGraphState(TypedDict, total=False):
    """
    Shared state for the orchestrator graph.

    Fields:
      - run_id:     Unique identifier for the run (UUID string).
      - scenario:   ScenarioType enum value for this run.
      - status:     High-level RunStatus (pending/running/awaiting_approval/...).
      - run_context:Shared in-memory context between agents; matches the
                    conceptual structure used in agents/orchestrator_live.py.
      - started_at: Unix timestamp (float) when the graph started.
    """

    run_id: str
    scenario: ScenarioType
    status: RunStatus
    run_context: Dict[str, Any]
    started_at: float


__all__ = ["RunGraphState"]

