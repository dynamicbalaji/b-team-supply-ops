"""
agents/base.py
──────────────
Shared infrastructure for all 5 agents.

Model chain fallback (configurable via .env)
─────────────────────────────────────────────
stream_gemini() walks through GEMINI_MODEL_CHAIN trying each model in
order. It moves to the next model on:

  • Rate limit / quota exceeded  (429 / ResourceExhausted)
  • Model not found / unsupported (404)
  • Server / overload error       (500 / 503)
  • Per-model timeout             (GEMINI_MODEL_TIMEOUT seconds)
  • Any other unexpected exception

It stops the chain only on safety blocks (same block on all models).
After exhausting all models it emits _FALLBACK_TEXTS as token events.

All significant events are written via _log() which calls BOTH
logging.getLogger() AND print() so output is always visible regardless
of whether the caller has configured Python logging.

.env knobs:
  GEMINI_MODEL_CHAIN=gemini-2.0-flash,gemini-2.5-flash-preview-05-20,...
  GEMINI_MODEL_TIMEOUT=20
  GEMINI_RATE_LIMIT_RETRIES=2
  GEMINI_RATE_LIMIT_BACKOFF=1.5
"""

import asyncio
import time
import logging
import sys

import db.redis_client as redis_client
from core.models import (
    AgentId, AgentStatus,
    AgentStateEvent, MessageEvent, TokenEvent, ToolEvent,
)
from core.config import get_settings

_logger = logging.getLogger("resolveiq.agents")


# ─────────────────────────────────────────────────────────────────────────
# Dual-output logger: always prints, also feeds the logging system
# ─────────────────────────────────────────────────────────────────────────

def _log(level: str, msg: str, *args) -> None:
    """
    Write to BOTH sys.stdout (guaranteed) and the Python logging system
    (only visible if a handler has been attached, which main.py does).

    level: "INFO" | "WARN" | "ERROR" | "DEBUG"
    """
    formatted = msg % args if args else msg
    # stdout — always visible in terminal / uvicorn logs
    prefix = {
        "DEBUG": "   ",
        "INFO":  "   ",
        "WARN":  "⚠️ ",
        "ERROR": "❌ ",
    }.get(level, "   ")
    print(f"{prefix}[agents] {formatted}", flush=True)
    # logging system — visible if main.py's _setup_logging() ran
    getattr(_logger, level.lower() if level != "WARN" else "warning")(formatted)


# ─────────────────────────────────────────────────────────────────────────
# Gemini library initialisation
# ─────────────────────────────────────────────────────────────────────────

_model_cache:      dict[str, object] = {}
_genai_configured: bool = False

_GENERATION_CONFIG = {
    "temperature":       0.7,
    "top_p":             0.9,
    "max_output_tokens": 300,
}

_SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT",       "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH",       "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]


def _configure_genai() -> bool:
    global _genai_configured
    if _genai_configured:
        return True
    cfg = get_settings()
    key = cfg.gemini_api_key
    if not key or key == "your_gemini_api_key_here":
        return False
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        _genai_configured = True
        _log("INFO", "google.generativeai configured (key length: %d)", len(key))
        return True
    except Exception as exc:
        _log("WARN", "google.generativeai configure failed: %s", exc)
        return False


def _get_model(model_name: str):
    if model_name in _model_cache:
        return _model_cache[model_name]
    if not _configure_genai():
        return None
    try:
        import google.generativeai as genai
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=_GENERATION_CONFIG,
            safety_settings=_SAFETY_SETTINGS,
        )
        _model_cache[model_name] = model
        return model
    except Exception as exc:
        _log("WARN", "Could not create model client for '%s': %s", model_name, exc)
        _model_cache[model_name] = None
        return None


# ─────────────────────────────────────────────────────────────────────────
# Error classification
# ─────────────────────────────────────────────────────────────────────────

def _is_rate_limit(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(t in msg for t in (
        "429", "resource_exhausted", "resourceexhausted",
        "quota", "rate limit", "ratelimit", "too many requests",
    ))


def _is_model_unavailable(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(t in msg for t in (
        "404", "not found", "notfound", "model not found",
        "not supported", "does not exist", "invalid model",
        "is not supported",
    ))


def _is_server_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(t in msg for t in (
        "500", "503", "internal", "service_unavailable",
        "serviceexception", "server error", "overloaded",
    ))


def _is_safety_block(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(t in msg for t in (
        "safety", "blocked", "finish_reason_safety",
        "harm_category", "recitation",
    ))


# ─────────────────────────────────────────────────────────────────────────
# Single-model attempt with rate-limit retry
# ─────────────────────────────────────────────────────────────────────────

async def _try_model(
    model_name:  str,
    prompt:      str,
    run_id:      str,
    agent:       AgentId,
    emit_tokens: bool,
) -> str | None:
    """
    Attempt one model. Retries on rate-limit. Returns text or None.
    Never raises.
    """
    model = _get_model(model_name)
    if model is None:
        _log("WARN", "[%s] %-32s  client unavailable — skipping", agent, model_name)
        return None

    cfg         = get_settings()
    max_retries = cfg.gemini_rate_limit_retries
    backoff     = cfg.gemini_rate_limit_backoff
    timeout_s   = cfg.gemini_model_timeout

    for attempt in range(max_retries + 1):
        try:
            full_text = ""

            async def _stream() -> str:
                nonlocal full_text
                response = await model.generate_content_async(prompt, stream=True)
                async for chunk in response:
                    if getattr(chunk, "text", None):
                        full_text += chunk.text
                        if emit_tokens:
                            await redis_client.publish(run_id, TokenEvent(
                                agent=agent, content=chunk.text
                            ).model_dump())
                        await asyncio.sleep(0)
                return full_text.strip()

            result = await asyncio.wait_for(_stream(), timeout=timeout_s)

            if not result:
                if attempt < max_retries:
                    _log("WARN", "[%s] %-32s  empty response (attempt %d) — retrying",
                         agent, model_name, attempt + 1)
                    await asyncio.sleep(backoff)
                    continue
                _log("WARN", "[%s] %-32s  empty response after all retries — skipping",
                     agent, model_name)
                return None

            _log("INFO", "[%s] %-32s  ✅ SUCCESS  (%d chars)", agent, model_name, len(result))
            return result

        except asyncio.TimeoutError:
            _log("WARN", "[%s] %-32s  ⏱ TIMEOUT after %ds — skipping",
                 agent, model_name, timeout_s)
            return None

        except Exception as exc:
            if _is_safety_block(exc):
                _log("WARN", "[%s] %-32s  🚫 SAFETY BLOCK — stopping chain: %s",
                     agent, model_name, exc)
                return None   # stops entire chain

            if _is_model_unavailable(exc):
                _log("WARN", "[%s] %-32s  🔍 MODEL NOT FOUND / UNSUPPORTED — skipping: %s",
                     agent, model_name, exc)
                return None

            if _is_server_error(exc):
                _log("WARN", "[%s] %-32s  💥 SERVER ERROR — skipping: %s",
                     agent, model_name, exc)
                return None

            if _is_rate_limit(exc):
                if attempt < max_retries:
                    wait = backoff * (2 ** attempt)
                    _log("WARN",
                         "[%s] %-32s  🔄 RATE LIMIT (attempt %d/%d) — retrying in %.1fs",
                         agent, model_name, attempt + 1, max_retries + 1, wait)
                    await asyncio.sleep(wait)
                    continue
                _log("WARN", "[%s] %-32s  🔄 RATE LIMIT retries exhausted — skipping",
                     agent, model_name)
                return None

            _log("WARN", "[%s] %-32s  ❓ UNEXPECTED ERROR (attempt %d): %s",
                 agent, model_name, attempt + 1, exc)
            return None

    return None


# ─────────────────────────────────────────────────────────────────────────
# Hardcoded fallback texts
# ─────────────────────────────────────────────────────────────────────────

_FALLBACK_TEXTS: dict[str, str] = {
    AgentId.LOGISTICS: (
        "Evaluated 3 freight options. Hybrid 60/40 at $280K / 36h is optimal "
        "given strike conditions and the March 2024 Long Beach precedent."
    ),
    AgentId.FINANCE: (
        "Monte Carlo over 100 iterations confirms Hybrid at $280K — 94% CI. "
        "Air-only breaches budget cap once the $50K customs surcharge is included."
    ),
    AgentId.PROCUREMENT: (
        "Dallas spot buy covers 80% of order quantity at $380K / 12h. "
        "Insufficient for full order — hybrid route fills the gap. Acknowledging consensus."
    ),
    AgentId.SALES: (
        "Apple confirmed 36h extension in writing. Zero penalty. "
        "Q3 priority allocation secured. Hybrid timeline fits the new SLA perfectly."
    ),
    AgentId.RISK: (
        "⚠ Consensus challenge: LAX ground crew availability is unconfirmed during "
        "active ILWU action — single point of failure. "
        "Recommend Hour-20 backup trigger to Tucson routing."
    ),
    AgentId.ORCHESTRATOR: (
        "Crisis P0 broadcast complete. All agents active. Awaiting parallel evaluation."
    ),
}


async def _emit_fallback_tokens(
    run_id: str, agent: AgentId, text: str, emit_tokens: bool
) -> None:
    if not emit_tokens:
        return
    for word in text.split():
        await redis_client.publish(run_id, TokenEvent(
            agent=agent, content=word + " "
        ).model_dump())
        await asyncio.sleep(0.06)


# ─────────────────────────────────────────────────────────────────────────
# Public API: stream_gemini
# ─────────────────────────────────────────────────────────────────────────

async def stream_gemini(
    run_id:      str,
    agent:       AgentId,
    prompt:      str,
    emit_tokens: bool = True,
) -> str:
    """
    Walk GEMINI_MODEL_CHAIN in order, returning the first successful response.
    Falls back to hardcoded text only when every model fails.
    Every decision is logged to stdout so you can see exactly what happened.
    """
    cfg   = get_settings()
    chain = cfg.model_chain

    _log("INFO", "[%s] Starting model chain  (%d models): %s",
         agent, len(chain), " → ".join(chain) if chain else "(empty)")

    if not chain:
        _log("WARN", "[%s] Chain is empty — emitting hardcoded fallback immediately.", agent)
        fallback = _FALLBACK_TEXTS.get(agent, "Processing...")
        await _emit_fallback_tokens(run_id, agent, fallback, emit_tokens)
        return fallback

    for i, model_name in enumerate(chain):
        is_last = (i + 1 == len(chain))
        _log("INFO", "[%s] Trying model %d/%d: %s", agent, i + 1, len(chain), model_name)

        # Diagnostic event — the frontend ignores unknown SSE types
        await redis_client.publish(run_id, {
            "type":       "model_attempt",
            "agent":      agent,
            "model":      model_name,
            "attempt":    i + 1,
            "chain_size": len(chain),
        })

        result = await _try_model(model_name, prompt, run_id, agent, emit_tokens)

        if result is not None:
            _log("INFO", "[%s] Chain resolved on model %d/%d: %s",
                 agent, i + 1, len(chain), model_name)
            await redis_client.publish(run_id, {
                "type":  "model_success",
                "agent": agent,
                "model": model_name,
            })
            return result

        if is_last:
            _log("ERROR", "[%s] All %d models exhausted — emitting hardcoded fallback.",
                 agent, len(chain))
        else:
            _log("WARN", "[%s] %s failed → next: %s", agent, model_name, chain[i + 1])

    # Every model failed
    await redis_client.publish(run_id, {
        "type":   "model_fallback",
        "agent":  agent,
        "reason": "all models in chain exhausted",
    })
    fallback = _FALLBACK_TEXTS.get(agent, "Processing...")
    _log("WARN", "[%s] Hardcoded fallback text: '%s...'", agent, fallback[:60])
    await _emit_fallback_tokens(run_id, agent, fallback, emit_tokens)
    return fallback


# ─────────────────────────────────────────────────────────────────────────
# Publish helpers
# ─────────────────────────────────────────────────────────────────────────

async def publish_state(
    run_id: str, agent: AgentId, status: AgentStatus,
    tool: str = "", confidence: float | None = None, pulsing: bool = True,
) -> None:
    await redis_client.publish(run_id, AgentStateEvent(
        agent=agent, status=status, tool=tool,
        confidence=confidence, pulsing=pulsing,
    ).model_dump())


async def publish_msg(
    run_id: str, agent: AgentId, from_label: str, to_label: str,
    timestamp: str, css_class: str, text: str, tools: list[str] | None = None,
) -> None:
    await redis_client.publish(run_id, MessageEvent(
        agent=agent, from_label=from_label, to_label=to_label,
        timestamp=timestamp, css_class=css_class,
        text=text, tools=tools or [],
    ).model_dump())


async def publish_tool(run_id: str, agent: AgentId, tool: str, result: dict) -> None:
    await redis_client.publish(run_id, ToolEvent(
        agent=agent, tool=tool, result=result,
    ).model_dump())


# ─────────────────────────────────────────────────────────────────────────
# Utility
# ─────────────────────────────────────────────────────────────────────────

def elapsed(start_time: float) -> str:
    secs = int(time.time() - start_time)
    return f"{secs // 60:02d}:{secs % 60:02d}"


def active_model_chain() -> list[str]:
    """Returns the current resolved chain — used by the /health endpoint."""
    return get_settings().model_chain


# ─────────────────────────────────────────────────────────────────────────
# Phase 3: Rich tool-result publisher
# ─────────────────────────────────────────────────────────────────────────

async def publish_tool_result(
    run_id: str,
    agent:  AgentId,
    tool:   str,
    raw:    dict | list | None,
) -> None:
    """
    Formats raw tool output into a display shape and emits ToolResultEvent.

    Emits TWO events:
      1. ToolEvent    (type="tool")        — keeps agent card pill working (Phase 2 compat)
      2. ToolResultEvent (type="tool_result") — new rich bubble in the chat log (Phase 3)

    Agents should call this instead of publish_tool() directly.
    """
    from tools.registry import format_tool_result
    from core.models import ToolResultEvent

    # 1. Legacy event — keeps tp-log / tp-fin pill updating
    await redis_client.publish(run_id, {
        "type":   "tool",
        "agent":  agent,
        "tool":   tool,
        "result": raw,
    })

    # 2. Rich display event — new in Phase 3
    display = format_tool_result(tool, raw)
    await redis_client.publish(run_id, ToolResultEvent(
        agent=agent,
        tool=tool,
        display=display,
        result=raw,
    ).model_dump())
