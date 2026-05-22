"""LiteRT inference service wrapper (based on DocuDog pattern)."""

import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)


class LiteRTInferenceError(Exception):
    """LiteRT inference failure with context."""

    def __init__(self, stage: str, cause: BaseException) -> None:
        self.stage = stage
        self.cause = cause
        super().__init__(f"{stage}: {cause}")


class LiteRTService:
    """Wrapper around litert_lm for Korean language tutoring."""

    def __init__(self, bundle_path: str, max_tokens: int = 512) -> None:
        """Initialize LiteRT engine.

        Args:
            bundle_path: Path to .litertlm bundle file
            max_tokens: Maximum output tokens
        """
        if not os.path.isfile(bundle_path):
            raise FileNotFoundError(f"Bundle not found: {bundle_path}")

        self.bundle_path = bundle_path
        self.max_tokens = max_tokens
        self.litert_lm: Any = None
        self.engine: Any = None

        self._init_litert()

    def _init_litert(self) -> None:
        """Load litert_lm module and set environment."""
        try:
            # Set LiteRT environment defaults (from DocuDog pattern)
            os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
            os.environ.setdefault("GLOG_minloglevel", "2")
            os.environ.setdefault("GOOGLE_LOG_LEVEL", "2")

            import litert_lm  # type: ignore[import-untyped]

            self.litert_lm = litert_lm
            logger.info(f"LiteRT module loaded successfully")
        except ImportError as e:
            raise LiteRTInferenceError("import_litert_lm", e) from e

    def _create_engine(self) -> Any:
        """Create or reuse LiteRT engine (lazy init)."""
        if self.engine is not None:
            return self.engine

        try:
            # Try with max_num_tokens parameter (preferred)
            try:
                self.engine = self.litert_lm.Engine(
                    self.bundle_path, max_num_tokens=self.max_tokens
                )
            except TypeError:
                # Fallback for older LiteRT versions
                self.engine = self.litert_lm.Engine(self.bundle_path)

            logger.info(
                f"LiteRT Engine created: {os.path.basename(self.bundle_path)}"
            )
            return self.engine
        except Exception as e:
            raise LiteRTInferenceError("create_engine", e) from e

    def complete(self, prompt: str, system: str = "") -> str:
        """Generate text completion.

        Args:
            prompt: User prompt
            system: System instruction

        Returns:
            Generated text response
        """
        full_prompt = f"{system}\n\n{prompt}" if system else prompt

        try:
            engine = self._create_engine()

            with engine as eng:
                with eng.create_conversation() as conv:
                    msg = conv.send_message(full_prompt)
                    response = self._extract_text(msg)

            if not response.strip():
                logger.warning("Empty response from LiteRT")
                return "죄송합니다. 응답을 생성할 수 없습니다."

            return response
        except LiteRTInferenceError:
            raise
        except Exception as e:
            raise LiteRTInferenceError("inference", e) from e

    @staticmethod
    def _extract_text(message: dict[str, Any]) -> str:
        """Extract text from LiteRT message response.

        Response format: {"content": [{"type": "text", "text": "..."}]}
        """
        content = message.get("content", [])
        if not isinstance(content, list):
            return ""

        text_parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))

        return "".join(text_parts).strip()
