"""Ground-truth evaluation metrics."""

from collections import Counter
from pathlib import Path
from typing import Mapping

import pandas as pd

from app.schemas import Category, Priority, TriageDecision


def load_ground_truth(path: str | Path) -> pd.DataFrame:
    """Load and validate a ground-truth CSV."""
    csv_path = Path(path)
    if not csv_path.is_file():
        raise FileNotFoundError(f"Ground-truth CSV not found: {csv_path}")

    frame = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    required = {"id", "category", "priority"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(
            f"Missing ground-truth columns: {', '.join(sorted(missing))}"
        )
    if frame["id"].duplicated().any():
        raise ValueError("Ground-truth CSV contains duplicate ids")

    allowed_categories = {item.value for item in Category}
    allowed_priorities = {item.value for item in Priority}
    unknown_categories = set(frame["category"]) - allowed_categories
    unknown_priorities = set(frame["priority"]) - allowed_priorities
    if unknown_categories:
        raise ValueError(
            f"Unknown ground-truth categories: {sorted(unknown_categories)}"
        )
    if unknown_priorities:
        raise ValueError(
            f"Unknown ground-truth priorities: {sorted(unknown_priorities)}"
        )
    return frame


def evaluate_ground_truth(
    decisions: list[TriageDecision],
    ground_truth: pd.DataFrame | Mapping[str, tuple[str, str]],
) -> dict[str, object]:
    """Compute real accuracy and confusion counts for auto-resolved tickets."""
    if isinstance(ground_truth, pd.DataFrame):
        truth = ground_truth.set_index("id")
        truth_by_id = {
            str(ticket_id): (str(row["category"]), str(row["priority"]))
            for ticket_id, row in truth.iterrows()
        }
    else:
        truth_by_id = {
            str(ticket_id): (str(category), str(priority))
            for ticket_id, (category, priority) in ground_truth.items()
        }

    category_correct = 0
    priority_correct = 0
    exact_correct = 0
    evaluated = 0
    category_confusion: Counter[str] = Counter()
    priority_confusion: Counter[str] = Counter()

    for decision in decisions:
        if decision.needs_review:
            continue
        if decision.category is None or decision.priority is None:
            continue
        if decision.id not in truth_by_id:
            continue

        expected_category, expected_priority = truth_by_id[decision.id]
        predicted_category = decision.category.value
        predicted_priority = decision.priority.value

        evaluated += 1
        category_match = predicted_category == expected_category
        priority_match = predicted_priority == expected_priority
        category_correct += int(category_match)
        priority_correct += int(priority_match)
        exact_correct += int(category_match and priority_match)
        category_confusion[f"{expected_category}->{predicted_category}"] += 1
        priority_confusion[f"{expected_priority}->{predicted_priority}"] += 1

    if evaluated == 0:
        return {
            "evaluated_auto_resolved": 0,
            "category_accuracy": None,
            "priority_accuracy": None,
            "exact_match_accuracy": None,
            "category_confusion": {},
            "priority_confusion": {},
        }

    return {
        "evaluated_auto_resolved": evaluated,
        "category_accuracy": category_correct / evaluated,
        "priority_accuracy": priority_correct / evaluated,
        "exact_match_accuracy": exact_correct / evaluated,
        "category_confusion": dict(sorted(category_confusion.items())),
        "priority_confusion": dict(sorted(priority_confusion.items())),
    }
