"""Command-line entry point for support ticket triage."""

import argparse
from dataclasses import replace
import logging
from pathlib import Path
from typing import Sequence

import pandas as pd
from dotenv import load_dotenv

from app.config import Settings
from app.llm.factory import get_client
from app.pipeline import run_pipeline
from app.preprocess import load_tickets
from app.review import write_review_queue
from app.report import write_run_report


LOGGER = logging.getLogger(__name__)


def build_parser(settings: Settings) -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Run support ticket triage."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(settings.DEFAULT_INPUT_PATH),
        help="Path to the input CSV.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(settings.DEFAULT_OUTPUT_DIR),
        help="Directory for output files.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=settings.CONCURRENCY,
        help="Maximum concurrent ticket processing tasks.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of input tickets.",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use the deterministic mock LLM client.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the triage pipeline and write output files."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    load_dotenv()
    settings = Settings.from_env()
    args = build_parser(settings).parse_args(argv)
    if args.limit is not None and args.limit < 0:
        LOGGER.error("--limit must be zero or greater")
        return 2
    if args.concurrency <= 0:
        LOGGER.error("--concurrency must be positive")
        return 2

    settings = replace(settings, CONCURRENCY=args.concurrency)
    client = get_client(settings, mock=args.mock)
    tickets = load_tickets(args.input)
    if args.limit is not None:
        tickets = tickets[:args.limit]

    LOGGER.info("Processing %d tickets", len(tickets))
    decisions = run_pipeline(tickets, client, settings)

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    results_rows = [
        {
            "id": decision.id,
            "category": (
                "" if decision.needs_review or decision.category is None
                else decision.category.value
            ),
            "priority": (
                "" if decision.needs_review or decision.priority is None
                else decision.priority.value
            ),
            "needs_review": "yes" if decision.needs_review else "no",
        }
        for decision in decisions
    ]
    results = pd.DataFrame(
        results_rows,
        columns=["id", "category", "priority", "needs_review"],
    )
    if len(results) != len(tickets):
        raise AssertionError(
            f"results.csv row count {len(results)} does not match input count {len(tickets)}"
        )
    results.to_csv(output_dir / "results.csv", index=False)

    details = pd.DataFrame(
        [decision.model_dump(mode="json") for decision in decisions],
        columns=[
            "id",
            "category",
            "priority",
            "needs_review",
            "review_reasons",
            "source",
            "suggested_category",
            "suggested_priority",
            "confidence",
            "latency_ms",
            "attempts",
            "error",
        ],
    )
    details.to_csv(output_dir / "details.csv", index=False)

    write_review_queue(decisions, tickets, output_dir / "review_queue.csv")
    write_run_report(decisions, decisions, output_dir / "run_report.json")
    LOGGER.info("Wrote outputs to %s", output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
