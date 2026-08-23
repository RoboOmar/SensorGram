import asyncio
from typing import AsyncGenerator

# Global SSE subscriber list: list of asyncio.Queue objects
_subscribers: list[asyncio.Queue] = []


def get_subscribers():
    return _subscribers


async def subscribe() -> tuple[asyncio.Queue, int]:
    q: asyncio.Queue = asyncio.Queue(maxsize=100)
    _subscribers.append(q)
    return q, id(q)


def unsubscribe(q: asyncio.Queue):
    try:
        _subscribers.remove(q)
    except ValueError:
        pass


async def broadcast(event_type: str, data: dict):
    """Broadcast a JSON-serialisable payload to all SSE subscribers."""
    import json
    payload = json.dumps({"type": event_type, "data": data})
    dead = []
    for q in list(_subscribers):
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        unsubscribe(q)


async def event_generator(q: asyncio.Queue) -> AsyncGenerator[str, None]:
    """Yields SSE-formatted strings from the queue."""
    try:
        while True:
            payload = await asyncio.wait_for(q.get(), timeout=25)
            yield f"data: {payload}\n\n"
    except asyncio.TimeoutError:
        yield ": ping\n\n"  # keep-alive comment
