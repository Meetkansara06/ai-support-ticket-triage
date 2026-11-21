"""OpenAI implementation of the LLMClient interface."""

import os

from openai import OpenAI

from app.llm.base import LLMClient, LLMRateLimitError, LLMServerError, LLMTimeoutError


class OpenAIClient(LLMClient):
    """OpenAI JSON-mode client."""

    def __init__(self, model_name: str) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is missing. Set it in the environment or rerun with --mock."
            )
        self.model_name = model_name
        self.client = OpenAI(api_key=api_key, timeout=20)

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        timeout_s: int,
    ) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
                response_format={"type": "json_object"},
                timeout=timeout_s,
            )
            return response.choices[0].message.content or ""
        except TimeoutError as exc:
            raise LLMTimeoutError("OpenAI request timed out") from exc
        except Exception as exc:
            status = getattr(exc, "status_code", None)
            if status == 429:
                raise LLMRateLimitError("OpenAI rate limit") from exc
            if status is not None and 500 <= int(status) < 600:
                raise LLMServerError("OpenAI server error") from exc
            raise
