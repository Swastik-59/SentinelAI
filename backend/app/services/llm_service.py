"""
SentinelAI — LLM Service (Ollama Mistral Integration)

Connects to a local Ollama instance running the Mistral model to:
- Generate human-readable explanation summaries
- Suggest mitigation steps for flagged content

Requirements:
- Ollama installed and running locally
- Model: mistral (run `ollama pull mistral`)

API: POST http://localhost:11434/api/generate
"""

import os
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))  # seconds (CPU inference needs more time)

# Reusable async HTTP client
_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    """Get or create a reusable async HTTP client."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=httpx.Timeout(OLLAMA_TIMEOUT))
    return _client


async def check_ollama_health() -> bool:
    """Check if Ollama is running and accessible."""
    try:
        client = _get_client()
        response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
        return response.status_code == 200
    except Exception:
        return False


async def generate_explanation(
    text: str,
    ai_probability: float,
    fraud_probability: float,
    risk_score: float,
    risk_level: str,
) -> str:
    """
    Use Ollama Mistral to generate a human-readable explanation
    of why content was flagged, plus mitigation steps.

    Returns explanation string, or empty string on failure.
    """
    prompt = _build_prompt(text, ai_probability, fraud_probability, risk_score, risk_level)

    try:
        client = _get_client()
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "num_predict": 300,
                },
            },
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("response", "").strip()
        else:
            logger.warning(
                "Ollama returned status %d: %s",
                response.status_code,
                response.text[:200],
            )
            return ""

    except httpx.TimeoutException:
        logger.warning("Ollama request timed out after %.0fs", OLLAMA_TIMEOUT)
        return ""
    except httpx.ConnectError:
        logger.warning("Could not connect to Ollama at %s", OLLAMA_BASE_URL)
        return ""
    except Exception as e:
        logger.warning("Ollama LLM generation failed: %s", e)
        return ""


def _build_prompt(
    text: str,
    ai_probability: float,
    fraud_probability: float,
    risk_score: float,
    risk_level: str,
) -> str:
    """Build the analysis prompt for Mistral."""
    return f"""You are a banking fraud analysis expert. Analyze the following content and explain the risk assessment.

CONTENT (first 500 chars):
\"\"\"{text[:500]}\"\"\"

ANALYSIS SCORES:
- AI Generation Probability: {ai_probability:.1%}
- Fraud Probability: {fraud_probability:.1%}
- Combined Risk Score: {risk_score:.2f}
- Risk Level: {risk_level}

Provide a concise explanation (3-5 sentences) covering:
1. Why this content was flagged at this risk level
2. Key indicators that contributed to the score
3. Recommended mitigation steps

Be specific and actionable. Do not repeat the scores verbatim."""


async def close_client() -> None:
    """Close the HTTP client on shutdown."""
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None
