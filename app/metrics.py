"""Metrics computed from real pipeline decisions."""

from collections import Counter
import math

from app.pipeline import PipelineDecisions
from app.schemas import TriageDecision


def _p95(values: list[int]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(math.ceil(0.95 * len(ordered)) - 1, 0)
    return float(ordered[index])


def compute_metrics(
    decisions: list[TriageDecision],
    pipeline_stats: PipelineDecisions | None = None,
) -> dict[str, object]:
    """Compute run metrics solely from pipeline output."""
    total = len(decisions)
    review_count = sum(decision.needs_review for decision in decisions)
    auto_count = total - review_count

    reason_counts = Counter(
        reason
        for decision in decisions
        for reason in decision.review_reasons
    )
    category_distribution = Counter(
        decision.category.value
        for decision in decisions
        if not decision.needs_review and decision.category is not None
    )
    priority_distribution = Counter(
        decision.priority.value
        for decision in decisions
        if not decision.needs_review and decision.priority is not None
    )

    latencies = [decision.latency_ms for decision in decisions]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    source_counts = Counter(decision.source for decision in decisions)

    if pipeline_stats is not None:
        llm_success = pipeline_stats.llm_successes + pipeline_stats.cache_hits
        llm_failure = pipeline_stats.llm_failures
        retries = pipeline_stats.retries
        cache_hits = pipeline_stats.cache_hits
        estimated_tokens = pipeline_stats.estimated_tokens
    else:
        llm_success = sum(decision.source == "llm" for decision in decisions)
        llm_failure = sum(decision.source == "fallback" for decision in decisions)
        retries = sum(max(decision.attempts - 1, 0) for decision in decisions)
        cache_hits = 0
        estimated_tokens = 0

    return {
        "total": total,
        "auto_resolved": auto_count,
        "sent_to_review": review_count,
        "review_rate": (review_count / total) if total else 0.0,
        "review_reasons_count": dict(sorted(reason_counts.items())),
        "category_distribution_auto_resolved": dict(sorted(category_distribution.items())),
        "priority_distribution_auto_resolved": dict(sorted(priority_distribution.items())),
        "llm_success_count": llm_success,
        "llm_failure_count": llm_failure,
        "fallback_count": source_counts["fallback"],
        "retries": retries,
        "cache_hits": cache_hits,
        "avg_latency_ms": avg_latency,
        "p95_latency_ms": _p95(latencies),
        "total_estimated_tokens": estimated_tokens,
    }
