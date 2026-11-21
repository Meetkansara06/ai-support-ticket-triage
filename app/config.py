"""Environment-backed application settings."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    """Validated application configuration."""

    LLM_PROVIDER: str = "gemini"
    MODEL_NAME: str = ""
    CONFIDENCE_THRESHOLD: float = 0.75
    MAX_BODY_CHARS: int = 2000
    REQUEST_TIMEOUT_S: int = 20
    MAX_RETRIES: int = 3
    CONCURRENCY: int = 4
    DEFAULT_INPUT_PATH: str = "candidate/tickets.csv"
    DEFAULT_OUTPUT_DIR: str = "outputs"

    def __post_init__(self) -> None:
        if not 0.0 <= self.CONFIDENCE_THRESHOLD <= 1.0:
            raise ValueError("CONFIDENCE_THRESHOLD must be between 0 and 1")

        positive_int_settings = {
            "MAX_BODY_CHARS": self.MAX_BODY_CHARS,
            "REQUEST_TIMEOUT_S": self.REQUEST_TIMEOUT_S,
            "MAX_RETRIES": self.MAX_RETRIES,
            "CONCURRENCY": self.CONCURRENCY,
        }
        for name, value in positive_int_settings.items():
            if value <= 0:
                raise ValueError(f"{name} must be a positive integer")

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables."""

        def env_float(name: str, default: float) -> float:
            value = os.getenv(name)
            return default if value is None or value.strip() == "" else float(value)

        def env_int(name: str, default: int) -> int:
            value = os.getenv(name)
            return default if value is None or value.strip() == "" else int(value)

        def env_string(name: str, default: str) -> str:
            value = os.getenv(name)
            return default if value is None or value.strip() == "" else value

        try:
            settings = cls(
                LLM_PROVIDER=env_string("LLM_PROVIDER", "gemini"),
                MODEL_NAME=env_string("MODEL_NAME", ""),
                CONFIDENCE_THRESHOLD=env_float("CONFIDENCE_THRESHOLD", 0.75),
                MAX_BODY_CHARS=env_int("MAX_BODY_CHARS", 2000),
                REQUEST_TIMEOUT_S=env_int("REQUEST_TIMEOUT_S", 20),
                MAX_RETRIES=env_int("MAX_RETRIES", 3),
                CONCURRENCY=env_int("CONCURRENCY", 4),
                DEFAULT_INPUT_PATH=env_string("DEFAULT_INPUT_PATH", "candidate/tickets.csv"),
                DEFAULT_OUTPUT_DIR=env_string("DEFAULT_OUTPUT_DIR", "outputs"),
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid environment setting: {exc}") from exc
        return settings

    @classmethod
    def load(cls) -> "Settings":
        """Load settings, with the environment taking precedence over defaults."""
        return cls.from_env()


def get_settings() -> Settings:
    """Return validated settings loaded from the environment."""
    return Settings.from_env()
