"""Tests for triage decision routing."""

from app.decision import decide
from app.rules import RuleResult
from app.schemas import LLMTriageResult, Ticket


def make_ticket() -> Ticket:
    return Ticket(id="T-1", received_at="", customer="", subject="Test", body="Test body.")


def test_low_confidence_requires_review() -> None:
    llm_result = LLMTriageResult(
        category="Technical",
        priority="Medium",
        confidence=0.4,
        reason="Uncertain.",
    )
    decision = decide(
        make_ticket(),
        RuleResult(flags=[], skip_llm=False),
        llm_result,
        None,
        confidence_threshold=0.75,
        latency_ms=10,
        attempts=1,
    )
    assert decision.needs_review
    assert "low_confidence" in decision.review_reasons
    assert decision.category is None
    assert decision.priority is None


def test_urgent_requires_review() -> None:
    llm_result = LLMTriageResult(
        category="Technical",
        priority="Urgent",
        confidence=0.95,
        reason="Urgent outage.",
    )
    decision = decide(
        make_ticket(),
        RuleResult(flags=[], skip_llm=False),
        llm_result,
        None,
        confidence_threshold=0.75,
        latency_ms=10,
        attempts=1,
    )
    assert decision.needs_review
    assert "urgent_priority_requires_review" in decision.review_reasons


def test_fallback_requires_review() -> None:
    decision = decide(
        make_ticket(),
        RuleResult(flags=[], skip_llm=False),
        None,
        "timeout",
        confidence_threshold=0.75,
        latency_ms=10,
        attempts=3,
    )
    assert decision.needs_review
    assert decision.source == "fallback"
