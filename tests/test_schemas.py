"""Tests for triage Pydantic schemas."""

import pytest
from pydantic import ValidationError

from app.schemas import Category, LLMTriageResult, Priority


def test_valid_result_passes() -> None:
    result = LLMTriageResult(
        category="Billing",
        priority="High",
        confidence=0.8,
        reason="Payment appears to have failed.",
    )

    assert result.category is Category.BILLING
    assert result.priority is Priority.HIGH


def test_unknown_category_fails() -> None:
    with pytest.raises(ValidationError):
        LLMTriageResult(
            category="Security",
            priority="Low",
            confidence=0.9,
            reason="Unknown category.",
        )


def test_confidence_above_one_fails() -> None:
    with pytest.raises(ValidationError):
        LLMTriageResult(
            category="Technical",
            priority="Medium",
            confidence=1.2,
            reason="Confidence is out of range.",
        )


def test_extra_field_fails() -> None:
    with pytest.raises(ValidationError):
        LLMTriageResult.model_validate(
            {
                "category": "Account",
                "priority": "Urgent",
                "confidence": 0.95,
                "reason": "Account access is blocked.",
                "unexpected": True,
            }
        )


def test_category_and_priority_labels_are_exact() -> None:
    assert {category.value for category in Category} == {
        "Billing",
        "Technical",
        "Account",
        "Shipping",
        "Other",
    }
    assert {priority.value for priority in Priority} == {
        "Low",
        "Medium",
        "High",
        "Urgent",
    }
