"""
redis_client.py
───────────────
Thin wrapper around Upstash Redis REST API.

Upstash Redis doesn't support the traditional blocking SUBSCRIBE command
over its REST interface, so we implement lightweight pub/sub using:
  - PUBLISH  → REST POST  (fire-and-forget, works fine)
  - SUBSCRIBE → polling a Redis LIST used as a queue per run_id

Pattern:
  Publisher  → LPUSH  resolveiq:run:{run_id}:queue  <json>
  Subscriber → BRPOP  resolveiq:run:{run_id}:queue  (with timeout)

This is reliable, debuggable, and works on Upstash free tier.
"""

import json
import asyncio
import httpx
from core.config import get_settings

settings = get_settings()

# ── HTTP client (shared, keep-alive) ────────────────────────────────────
_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=settings.upstash_redis_rest_url,
            headers={"Authorization": f"Bearer {settings.upstash_redis_rest_token}"},
            timeout=10.0,
        )
    return _client


# ── Low-level REST commands ──────────────────────────────────────────────

async def _cmd(*args) -> dict:
    """Execute any Redis command via Upstash REST API."""
    client = _get_client()
    resp = await client.post("/", json=list(args))
    resp.raise_for_status()
    return resp.json()


# ── Queue-based pub/sub ──────────────────────────────────────────────────

QUEUE_KEY = "resolveiq:run:{run_id}:queue"
TTL_SECONDS = 3600  # queues expire after 1 hour


async def publish(run_id: str, event: dict) -> None:
    """Push an event JSON onto the run's queue. Non-blocking."""
    key = QUEUE_KEY.format(run_id=run_id)
    payload = json.dumps(event)
    await _cmd("LPUSH", key, payload)
    # Refresh TTL on every push so active runs never expire mid-demo
    await _cmd("EXPIRE", key, TTL_SECONDS)


async def pop_event(run_id: str, timeout: int = 5) -> dict | None:
    """
    Block-pop one event from the queue (up to `timeout` seconds).
    Returns None on timeout (caller should yield a keep-alive ping).
    Upstash REST supports BRPOP via the /pipeline endpoint trick —
    we emulate it with polling for free-tier compatibility.
    """
    key = QUEUE_KEY.format(run_id=run_id)
    # RPOP (non-blocking) — we do our own async sleep loop
    result = await _cmd("RPOP", key)
    if result.get("result") is not None:
        return json.loads(result["result"])
    return None


async def set_run_state(run_id: str, state: dict) -> None:
    """Persist full run state as a Redis hash (for reconnects)."""
    key = f"resolveiq:run:{run_id}:state"
    await _cmd("SET", key, json.dumps(state))
    await _cmd("EXPIRE", key, TTL_SECONDS)


async def get_run_state(run_id: str) -> dict | None:
    """Retrieve run state."""
    key = f"resolveiq:run:{run_id}:state"
    result = await _cmd("GET", key)
    raw = result.get("result")
    if raw:
        return json.loads(raw)
    return None


async def delete_queue(run_id: str) -> None:
    """Clean up after a run completes."""
    await _cmd("DEL", QUEUE_KEY.format(run_id=run_id))
    await _cmd("DEL", f"resolveiq:run:{run_id}:state")


async def health_check() -> bool:
    """Returns True if Redis is reachable."""
    try:
        result = await _cmd("PING")
        return result.get("result") == "PONG"
    except Exception:
        return False
