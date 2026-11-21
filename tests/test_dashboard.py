"""Tests for dashboard output loading and required CSV shape."""

import pandas as pd


def test_dashboard_outputs_are_readable() -> None:
    results = pd.read_csv(
        "outputs/results.csv",
        dtype=str,
        keep_default_na=False,
    )
    review = pd.read_csv(
        "outputs/review_queue.csv",
        dtype=str,
        keep_default_na=False,
    )

    assert list(results.columns) == [
        "id",
        "category",
        "priority",
        "needs_review",
    ]
    assert len(results) == 300
    assert "needs_review" in results.columns
    assert "id" in review.columns
