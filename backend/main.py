from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import logging

from backend.database import init_db
from backend.routers import auth, robots, posts, comments, stream, chat, ai_chat

app = FastAPI(
    title="SensorGram API",
    description="Instagram for robots — share your sensor data with the world.",
    version="1.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception Handler ─────────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled Exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc)},
    )

# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    init_db()
    # Ensure upload directory exists
    Path("uploads").mkdir(exist_ok=True)

# ── API Routers ───────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(robots.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(stream.router)
app.include_router(chat.router)
app.include_router(ai_chat.router)

# ── Static file serving ───────────────────────────────────────────────────────
# Serve uploaded media
# Ensure upload directory exists before mounting (StaticFiles checks at mount time)
Path("uploads").mkdir(exist_ok=True)

# Serve uploaded media
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

from pydantic import BaseModel
class TestEmailRequest(BaseModel):
    email: str

@app.post("/api/test-email")
async def test_email_route(req: TestEmailRequest):
    try:
        from backend.services.email_service import send_test_email
        await send_test_email(req.email)
        return {"status": "success", "message": f"Test email sent to {req.email}"}
    except Exception as e:
        from fastapi import HTTPException
        if isinstance(e, HTTPException):
            raise e
        error_type = type(e).__name__
        error_msg = str(e)
        return JSONResponse(
            status_code=500, 
            content={
                "detail": "Failed to send email", 
                "error_type": error_type,
                "error_message": error_msg
            }
        )

@app.get("/reset-password")
async def reset_password_page():
    from fastapi.responses import FileResponse
    return FileResponse("frontend/index.html")

# Serve the frontend SPA — must be last so it doesn't shadow API routes
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    from fastapi import HTTPException
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    
    logger.exception("Unhandled exception occurred: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. The backend is currently experiencing heavy load."}
    )
