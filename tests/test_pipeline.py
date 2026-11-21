"""Pipeline tests using the mock LLM client only."""

from app.config import Settings
from app.llm.mock import MockLLMClient
from app.pipeline import run_pipeline
from app.schemas import Ticket


def test_timeout_mock_finishes_batch_in_fallback() -> None:
    tickets = [
        Ticket(
            id="T-1",
            received_at="",
            customer="",
            subject="Login issue",
            body="I cannot log in to my account.",
        ),
        Ticket(
            id="T-2",
            received_at="",
            customer="",
            subject="Invoice",
            body="Please send me a copy of my invoice.",
        ),
    ]
    settings = Settings(CONCURRENCY=2, MAX_RETRIES=2)
    decisions = run_pipeline(tickets, MockLLMClient(timeout=True), settings)

    assert len(decisions) == 2
    assert all(decision.needs_review for decision in decisions)
    assert all(decision.source == "fallback" for decision in decisions)
