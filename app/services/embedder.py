import httpx
import logging
from app.config.settings import OPENROUTER_API_KEY, EMBEDDING_MODEL, EMBEDDING_DIMENSION

logger = logging.getLogger(__name__)


def create_embedding(text: str) -> list[float]:
    """
    Generates a text embedding vector via the OpenRouter API.
    Uses the configured model and dimension parameters.
    """
    if not OPENROUTER_API_KEY:
        # Fall back gracefully or log a warning if API key isn't provided during build/test,
        # but in actual use it must be present.
        logger.warning(
            "OPENROUTER_API_KEY environment variable is not configured. "
            "Falling back to a dummy zero-vector embedding for testing/development."
        )
        return [0.0] * EMBEDDING_DIMENSION

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": EMBEDDING_MODEL,
        "input": text,
        "dimensions": EMBEDDING_DIMENSION
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                "https://openrouter.ai/api/v1/embeddings",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            response_data = response.json()

            # OpenRouter is OpenAI-compatible for embeddings:
            return response_data["data"][0]["embedding"]
    except Exception as e:
        logger.error(f"Failed to generate embedding via OpenRouter API: {e}")
        raise