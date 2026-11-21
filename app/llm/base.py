"""LLM client interface and retryable exception types."""

from abc import ABC, abstractmethod


class LLMTimeoutError(TimeoutError):
    """Raised when an LLM request times out."""


class LLMRateLimitError(Exception):
    """Raised when an LLM provider applies rate limiting."""


class LLMServerError(Exception):
    """Raised for a provider 5xx response."""


class LLMClient(ABC):
    """Interface for JSON-generating LLM clients."""

    @abstractmethod
    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        timeout_s: int,
    ) -> str:
        """Generate a JSON string."""
        raise NotImplementedError
