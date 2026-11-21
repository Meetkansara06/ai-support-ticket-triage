"""Gemini implementation of the LLMClient interface."""

import os

from google import genai
from google.genai import types

from app.llm.base import LLMClient, LLMRateLimitError, LLMServerError, LLMTimeoutError


class GeminiClient(LLMClient):
    """Google Gemini JSON client."""

    def __init__(self, model_name: str) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is missing. Set it in the environment or rerun with --mock."
            )
        self.model_name = model_name
        self.client = genai.Client(api_key=api_key)

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        timeout_s: int,
    ) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0,
                    response_mime_type="application/json",
                    http_options=types.HttpOptions(timeout=timeout_s * 1000),
                ),
            )
            return response.text or ""
        except TimeoutError as exc:
            raise LLMTimeoutError("Gemini request timed out") from exc
        except Exception as exc:
            status = getattr(exc, "status_code", None)
            if status == 429:
                raise LLMRateLimitError("Gemini rate limit") from exc
            if status is not None and 500 <= int(status) < 600:
                raise LLMServerError("Gemini server error") from exc
            raise
