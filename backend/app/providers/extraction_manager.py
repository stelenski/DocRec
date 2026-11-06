import logging
import os

from app.providers.groq_provider import extract_with_groq
from app.providers.ollama_provider import extract_with_ollama

logger = logging.getLogger(__name__)

PROVIDERS = {
    "groq": extract_with_groq,
    "ollama": extract_with_ollama,
}


def extract_with_fallback(image_path: str, prompt: str) -> str:
    primary = os.getenv("AI_PROVIDER", "groq").lower()
    fallback = os.getenv("FALLBACK_PROVIDER", "ollama").lower()

    if primary not in PROVIDERS:
        raise ValueError(f"Unsupported primary provider: {primary}")
    if fallback not in PROVIDERS:
        raise ValueError(f"Unsupported fallback provider: {fallback}")

    primary_error = None
    try:
        logger.info("Attempting extraction using primary provider: %s", primary)
        result = PROVIDERS[primary](image_path, prompt)
        logger.info("Extraction successful using %s", primary)
        return result
    except Exception as exc:
        primary_error = exc
        logger.exception("Primary provider %s failed; trying %s", primary, fallback)
        if primary == fallback:
            raise RuntimeError(f"Primary provider failed: {exc}") from exc

    try:
        result = PROVIDERS[fallback](image_path, prompt)
        logger.info("Extraction successful using fallback provider: %s", fallback)
        return result
    except Exception as fallback_error:
        logger.exception("Fallback provider %s also failed", fallback)
        raise RuntimeError(
            f"Both providers failed. Primary: {primary_error}. "
            f"Fallback: {fallback_error}"
        ) from fallback_error
