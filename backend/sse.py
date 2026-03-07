"""
sse.py
──────
Server-Sent Events transport layer.

Responsibility: drain the Redis queue for a run and forward each event
to the connected browser as an SSE frame.

This module has NO knowledge of LangGraph, agents, or business logic.
It is a pure transport pipe:

    Redis queue (written by graph nodes via redis_client.publish)
        └─► _event_generator polls every POLL_INTERVAL seconds
               └─► yields "data: {...}\n\n" to the browser EventSource

The asyncio.sleep(POLL_INTERVAL) at the bottom of the generator loop is
an I/O polling interval — not orchestration.  It controls how often we
check Redis for new events, equivalent to a select() timeout in a
traditional socket server.  No business logic, no agent coordination,
and no timing decisions live here.

Browser connects with:
  const es = new EventSource(`/api/stream/${run_id}`);
  es.onmessage = (e) => handleEvent(JSON.parse(e.data));
"""

import asyncio
import json
from fastapi import Request
from fastapi.responses import StreamingResponse
import redis_client


POLL_INTERVAL   = 0.05   # 50 ms — snappy without hammering Redis
KEEPALIVE_SECS  = 15     # send a keep-alive SSE comment every N seconds
MAX_EMPTY_POLLS = int(KEEPALIVE_SECS / POLL_INTERVAL)


async def stream_run(run_id: str, request: Request) -> StreamingResponse:
    """
    Returns a StreamingResponse that the browser EventSource reads.
    Call this from the route handler; it has no knowledge of run internals.
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

    SSE wire format:
        data: {"type": "message", ...}\n\n
        : ping\n\n          ← keep-alive comment (browsers ignore SSE comments)

    Termination: stops when a {"type": "complete"} event is dequeued, or
    when the client disconnects.
    """
    empty_poll_count = 0

    while True:
        # ── Disconnect check ─────────────────────────────────────────────
        if await request.is_disconnected():
            break

        # ── Dequeue next event from Redis ─────────────────────────────────
        event = await redis_client.pop_event(run_id)

        if event is not None:
            empty_poll_count = 0
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            if event.get("type") == "complete":
                yield f"data: {json.dumps({'type': 'stream_end'})}\n\n"
                break

        else:
            empty_poll_count += 1
            if empty_poll_count >= MAX_EMPTY_POLLS:
                yield ": ping\n\n"   # SSE comment — keep TCP alive
                empty_poll_count = 0

        # I/O polling interval — not orchestration
        await asyncio.sleep(POLL_INTERVAL)
