"""K-Lyric AI FastAPI Backend with LiteRT inference."""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from services.litert_service import LiteRTService

# Load environment variables from .env
load_dotenv()

# Global inference service (lazy loaded)
litert_service: LiteRTService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context - no startup loading, lazy init on first request."""
    yield
    # Cleanup if needed
    global litert_service
    litert_service = None


app = FastAPI(title="K-Lyric AI", lifespan=lifespan)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002", "http://localhost:3001", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    """User chat message."""
    prompt: str
    system: str | None = None


class ChatResponse(BaseModel):
    """AI tutor response."""
    response: str


class StatusResponse(BaseModel):
    """Status response with model info."""
    status: str
    model: str | None = None
    loaded: bool


def _init_service() -> None:
    """Initialize LiteRT service on first use."""
    global litert_service
    if litert_service is not None:
        return

    bundle_path = os.getenv("LITERT_BUNDLE_PATH")
    if not bundle_path:
        raise RuntimeError("LITERT_BUNDLE_PATH not set in .env")

    litert_service = LiteRTService(bundle_path)


@app.get("/health")
async def health_check() -> StatusResponse:
    """Health check endpoint - shows model status without loading."""
    bundle_path = os.getenv("LITERT_BUNDLE_PATH")
    model_name = os.path.basename(bundle_path) if bundle_path else "unknown"

    return StatusResponse(
        status="ok",
        model=model_name,
        loaded=litert_service is not None,
    )


@app.post("/api/init")
async def init_model() -> StatusResponse:
    """Initialize the model (lazy load on demand)."""
    global litert_service
    if litert_service is not None:
        bundle_path = os.getenv("LITERT_BUNDLE_PATH")
        model_name = os.path.basename(bundle_path) if bundle_path else "gemma"
        return StatusResponse(
            status="already_loaded",
            model=model_name,
            loaded=True,
        )

    try:
        import time
        bundle_path = os.getenv("LITERT_BUNDLE_PATH")
        model_name = os.path.basename(bundle_path) if bundle_path else "gemma"

        # Log initialization start
        import logging
        logging.info(f"Starting model initialization: {model_name}")

        start_time = time.time()
        _init_service()
        elapsed = time.time() - start_time

        logging.info(f"Model initialized in {elapsed:.2f}s")

        return StatusResponse(
            status="initialized",
            model=model_name,
            loaded=True,
        )
    except Exception as e:
        import logging
        logging.error(f"Model initialization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tutor/chat")
async def tutor_chat(message: ChatMessage) -> ChatResponse:
    """AI tutor chat endpoint using LiteRT."""
    if not message.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    try:
        # Lazy init on first request
        _init_service()

        if litert_service is None:
            raise HTTPException(status_code=503, detail="LiteRT service initialization failed")

        response = litert_service.complete(
            prompt=message.prompt,
            system=message.system or "You are a warm Korean language tutor.",
        )
        return ChatResponse(response=response)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
