"""Confidence and rule-based routing decisions."""

from app.rules import RuleResult
from app.schemas import LLMTriageResult, Ticket, TriageDecision


def decide(
    ticket: Ticket,
    rule_result: RuleResult,
    llm_result: LLMTriageResult | None,
    error: str | None,
    *,
    confidence_threshold: float,
    latency_ms: int,
    attempts: int,
) -> TriageDecision:
    """Build a final decision and human-review reasons."""
    reasons: list[str] = []
    if rule_result.flags:
        reasons.extend(rule_result.flags)

    if error:
        reasons.append("llm_failed")
        source = "fallback"
    elif llm_result is None and rule_result.skip_llm:
        source = "rule"
    elif llm_result is None:
        reasons.append("no_llm_result")
        source = "fallback"
    elif rule_result.flags:
        source = "rule"
    else:
        source = "llm"

    if llm_result is not None:
        if llm_result.confidence < confidence_threshold:
            reasons.append("low_confidence")
        if llm_result.priority.value == "Urgent":
            reasons.append("urgent_priority_requires_review")

    needs_review = bool(reasons)
    suggested_category = llm_result.category if llm_result is not None else None
    suggested_priority = llm_result.priority if llm_result is not None else None

    if not needs_review:
        category = llm_result.category if llm_result is not None else None
        priority = llm_result.priority if llm_result is not None else None
    else:
        category = None
        priority = None

    return TriageDecision(
        id=ticket.id,
        category=category,
        priority=priority,
        needs_review=needs_review,
        review_reasons=reasons,
        source=source,
        suggested_category=suggested_category,
        suggested_priority=suggested_priority,
        confidence=llm_result.confidence if llm_result is not None else None,
        latency_ms=latency_ms,
        attempts=attempts,
        error=error,
    )
