"""
sse.py
──────
Server-Sent Events streaming endpoint.

The SSE generator:
  1. Polls the run's Redis queue for events
  2. Formats each event as "data: {json}\n\n"
  3. Sends keep-alive pings every 15s so browser doesn't close the connection
  4. Terminates cleanly on run completion or client disconnect

Browser connects with:
  const es = new EventSource(`/api/stream/${run_id}`);
  es.onmessage = (e) => handleEvent(JSON.parse(e.data));
"""

import asyncio
import json
from fastapi import Request
from fastapi.responses import StreamingResponse
import redis_client


POLL_INTERVAL  = 0.05   # 50ms polling — snappy without hammering Redis
KEEPALIVE_SECS = 15     # send ping comment every N seconds
MAX_EMPTY_POLLS = int(KEEPALIVE_SECS / POLL_INTERVAL)  # before a ping


async def stream_run(run_id: str, request: Request) -> StreamingResponse:
    """
    Returns a StreamingResponse that the browser's EventSource reads.
    Call this from the route handler.
    """
    return StreamingResponse(
        _event_generator(run_id, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control":               "no-cache",
            "X-Accel-Buffering":           "no",   # disable Nginx buffering
            "Access-Control-Allow-Origin": "*",
        },
    )


async def _event_generator(run_id: str, request: Request):
    """
    Async generator — yields SSE-formatted strings.

    SSE format:
        data: {"type": "message", ...}\n\n
        : ping\n\n          ← keep-alive comment (browser ignores)
    """
    empty_poll_count = 0

    while True:
        # ── Check if browser disconnected ────────────────────────────────
        if await request.is_disconnected():
            break

        # ── Poll Redis for next event ─────────────────────────────────────
        event = await redis_client.pop_event(run_id)

        if event is not None:
            empty_poll_count = 0
            payload = json.dumps(event, ensure_ascii=False)
            yield f"data: {payload}\n\n"

            # ── Terminal event: stop streaming ───────────────────────────
            if event.get("type") == "complete":
                yield f"data: {json.dumps({'type': 'stream_end'})}\n\n"
                break

        else:
            empty_poll_count += 1
            if empty_poll_count >= MAX_EMPTY_POLLS:
                # Send SSE comment (keep-alive) — browser ignores comments
                yield ": ping\n\n"
                empty_poll_count = 0

        await asyncio.sleep(POLL_INTERVAL)
