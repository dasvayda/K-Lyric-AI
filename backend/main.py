"""K-Lyric AI FastAPI Backend with LiteRT inference."""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from services.litert_service import LiteRTService, LiteRTInferenceError

# Load environment variables from .env
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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


class ErrorResponse(BaseModel):
    """Structured error response."""
    error: str
    code: str
    detail: str


class StatusResponse(BaseModel):
    """Status response with model info."""
    status: str
    model: str | None = None
    loaded: bool
    backend_version: str = "1.0"
    message: str = ""


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

    if not bundle_path:
        logger.warning("LITERT_BUNDLE_PATH not configured")
        return StatusResponse(
            status="error",
            model=None,
            loaded=False,
            message="LITERT_BUNDLE_PATH environment variable not set"
        )

    model_name = os.path.basename(bundle_path)

    if not os.path.isfile(bundle_path):
        logger.warning(f"Bundle file not found: {bundle_path}")
        return StatusResponse(
            status="error",
            model=model_name,
            loaded=False,
            message=f"Bundle file not found: {bundle_path}"
        )

    return StatusResponse(
        status="ok",
        model=model_name,
        loaded=litert_service is not None,
        message="Backend ready. Model is lazy-loaded on first request."
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
        logger.warning("Empty prompt received")
        raise HTTPException(
            status_code=400,
            detail="Prompt cannot be empty"
        )

    try:
        _init_service()

        if litert_service is None:
            logger.error("LiteRT service initialization failed")
            raise HTTPException(
                status_code=503,
                detail="AI tutor service initialization failed. Check LITERT_BUNDLE_PATH."
            )

        response = litert_service.complete(
            prompt=message.prompt,
            system=message.system or "You are a warm Korean language tutor.",
        )
        logger.info(f"Chat completed successfully")
        return ChatResponse(response=response)

    except LiteRTInferenceError as e:
        logger.error(f"LiteRT inference error at {e.stage}: {e.cause}")
        raise HTTPException(
            status_code=503,
            detail=f"AI inference failed: {e.stage}. Please check the model file."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {type(e).__name__}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
