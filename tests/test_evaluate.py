"""Tests for ground-truth evaluation using mock decisions."""

import pandas as pd
import pytest

from app.evaluate import evaluate_ground_truth, load_ground_truth
from app.schemas import Ticket, TriageDecision


def make_decision(
    ticket_id: str,
    category: str,
    priority: str,
    needs_review: bool = False,
) -> TriageDecision:
    """Build a mock triage decision."""
    return TriageDecision(
        id=ticket_id,
        category=None if needs_review else category,
        priority=None if needs_review else priority,
        needs_review=needs_review,
        review_reasons=["test"] if needs_review else [],
        source="rule" if needs_review else "llm",
        suggested_category=category,
        suggested_priority=priority,
        confidence=0.9,
        latency_ms=1,
        attempts=1,
    )


def test_evaluate_ground_truth_computes_real_metrics() -> None:
    decisions = [
        make_decision("T-1", "Billing", "High"),
        make_decision("T-2", "Technical", "Low"),
        make_decision("T-3", "Shipping", "Medium", needs_review=True),
    ]
    truth = pd.DataFrame(
        [
            {"id": "T-1", "category": "Billing", "priority": "High"},
            {"id": "T-2", "category": "Account", "priority": "Low"},
        ]
    )

    metrics = evaluate_ground_truth(decisions, truth)

    assert metrics["evaluated_auto_resolved"] == 2
    assert metrics["category_accuracy"] == 0.5
    assert metrics["priority_accuracy"] == 1.0
    assert metrics["exact_match_accuracy"] == 0.5


def test_load_ground_truth_rejects_unknown_category(tmp_path) -> None:
    csv_path = tmp_path / "ground_truth.csv"
    pd.DataFrame(
        [{"id": "T-1", "category": "Security", "priority": "High"}]
    ).to_csv(csv_path, index=False)

    with pytest.raises(ValueError, match="Unknown ground-truth categories"):
        load_ground_truth(csv_path)
