"""
backend/graph
─────────────

LangGraph-based graphs for the ResolveIQ backend.

This package will progressively become the single source of truth for
multi-agent orchestration and agent behaviour. Existing FastAPI routes
and orchestrator functions will delegate into these graphs.
"""

from .state import RunGraphState  # re-export for convenience

__all__ = ["RunGraphState"]

