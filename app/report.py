"""Pipeline run report generation and summary output."""

import json
import logging
from pathlib import Path

from app.metrics import compute_metrics
from app.pipeline import PipelineDecisions
from app.schemas import TriageDecision


LOGGER = logging.getLogger(__name__)


def write_run_report(
    decisions: list[TriageDecision],
    pipeline_stats: PipelineDecisions,
    path: str | Path,
) -> dict[str, object]:
    """Write and print a run report."""
    metrics = compute_metrics(decisions, pipeline_stats)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(metrics, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    LOGGER.info("Run summary")
    LOGGER.info("-" * 64)
    LOGGER.info("%-38s %s", "Metric", "Value")
    LOGGER.info("-" * 64)
    for key, value in metrics.items():
        LOGGER.info("%-38s %s", key, value)
    return metrics
