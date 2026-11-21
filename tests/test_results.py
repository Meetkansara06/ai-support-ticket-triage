"""Tests for required results.csv output shape."""

from pathlib import Path

import pandas as pd

from main import main


def test_mock_results_columns_and_row_count(tmp_path: Path) -> None:
    input_path = Path("candidate/tickets.csv")
    output_dir = tmp_path / "output"

    exit_code = main(
        [
            "--input",
            str(input_path),
            "--output-dir",
            str(output_dir),
            "--concurrency",
            "2",
            "--limit",
            "20",
            "--mock",
        ]
    )

    assert exit_code == 0
    frame = pd.read_csv(output_dir / "results.csv")
    assert list(frame.columns) == ["id", "category", "priority", "needs_review"]
    assert len(frame) == 20
