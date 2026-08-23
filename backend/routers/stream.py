from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.services.feed_service import subscribe, unsubscribe, event_generator

router = APIRouter(prefix="/api/stream", tags=["stream"])


@router.get("")
async def sse_feed():
    """Server-Sent Events endpoint — clients connect here for live feed updates."""
    q, qid = await subscribe()

    async def stream():
        try:
            while True:
                async for chunk in event_generator(q):
                    yield chunk
        finally:
            unsubscribe(q)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
