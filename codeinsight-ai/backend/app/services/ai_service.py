"""
AI service layer.

This is the only place in the codebase that talks to the AI provider.
Routes and repositories never call it directly - that's what keeps
this swappable without touching the rest of the app.

Currently backed by Google AI Studio (Gemini) over its REST API via
httpx, since Gemini's free tier (no credit card, ~1500 req/day on
Flash) is generous enough for local development and testing.
"""
import json
import logging

import httpx

from app.core.config import get_settings
from app.prompts.complexity_prompt import complexity_prompt
from app.prompts.explain_prompt import explain_prompt
from app.prompts.refactor_prompt import refactor_prompt
from app.prompts.review_prompt import review_prompt
from app.prompts.security_prompt import security_prompt
from app.prompts.testing_prompt import testing_prompt

logger = logging.getLogger(__name__)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

_PROMPT_BUILDERS = {
    "review": review_prompt,
    "security": security_prompt,
    "refactor": refactor_prompt,
    "explain": explain_prompt,
    "tests": testing_prompt,
    "complexity": complexity_prompt,
}


class AIServiceError(Exception):
    """Raised when the AI call fails or returns something we can't parse."""


class AIService:
    def __init__(self):
        settings = get_settings()
        if not settings.google_api_key:
            raise AIServiceError(
                "GOOGLE_API_KEY is not set. Add it to backend/.env - "
                "get a free key at https://aistudio.google.com/apikey - "
                "see .env.example."
            )
        self._api_key = settings.google_api_key
        self._model = settings.google_model
        self._client = httpx.Client(timeout=60)

    def analyze(self, review_type: str, language: str, code: str, model: str | None = None) -> dict:
        """
        Runs the requested analysis and returns parsed JSON.
        Raises AIServiceError on any failure so the route layer can
        turn it into a clean HTTP error. `model` overrides the
        configured default for this call only (used to honor a user's
        preferred-model setting).
        """
        builder = _PROMPT_BUILDERS.get(review_type)
        if builder is None:
            raise AIServiceError(f"Unknown review_type: {review_type}")

        prompt = builder(language, code)
        url = f"{GEMINI_API_BASE}/{model or self._model}:generateContent"

        try:
            response = self._client.post(
                url,
                headers={"x-goog-api-key": self._api_key},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.2,
                        "maxOutputTokens": 4096,
                        "responseMimeType": "application/json",
                    },
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            logger.warning("Gemini API returned HTTP %s", status)
            raise AIServiceError(f"AI provider request failed (HTTP {status}).") from exc
        except httpx.RequestError as exc:
            logger.warning("Gemini API request failed")
            raise AIServiceError("AI provider connection failed.") from exc
        try:
            data = response.json()
        except ValueError as exc:
            raise AIServiceError("AI provider returned invalid JSON.") from exc
        raw_text = self._extract_text(data)
        return self._parse_json(raw_text)

    @staticmethod
    def _extract_text(data: dict) -> str:
        try:
            candidates = data["candidates"]
            if not candidates:
                raise AIServiceError("Gemini returned no candidates - the prompt may have been blocked by safety filters.")
            parts = candidates[0]["content"]["parts"]
            return "".join(p.get("text", "") for p in parts).strip()
        except (KeyError, IndexError, TypeError, AttributeError) as exc:
            logger.error("Unexpected Gemini response shape")
            raise AIServiceError("Unexpected response shape from the AI provider.") from exc

    @staticmethod
    def _parse_json(raw_text: str) -> dict:
        # responseMimeType=application/json usually guarantees clean JSON,
        # but strip any stray ```json fences defensively anyway.
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse AI response as JSON")
            raise AIServiceError(
                "AI response was not valid JSON. This usually clears up on retry."
            ) from exc
