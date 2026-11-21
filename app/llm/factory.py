"""LLM client construction."""

from app.config import Settings
from app.llm.base import LLMClient
from app.llm.mock import MockLLMClient


def get_client(settings: Settings, mock: bool = False) -> LLMClient:
    """Create a configured real or mock LLM client."""
    if mock:
        return MockLLMClient()

    provider = settings.LLM_PROVIDER.lower()
    if provider == "gemini":
        from app.llm.gemini import GeminiClient

        return GeminiClient(settings.MODEL_NAME)
    if provider == "openai":
        from app.llm.openai import OpenAIClient

        return OpenAIClient(settings.MODEL_NAME)
    raise ValueError(
        f"Unsupported LLM_PROVIDER '{settings.LLM_PROVIDER}'. Use gemini or openai, "
        "or rerun with --mock."
    )
