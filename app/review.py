"""Human review queue management."""

from pathlib import Path

import pandas as pd

from app.schemas import Ticket, TriageDecision


def write_review_queue(
    decisions: list[TriageDecision],
    tickets: list[Ticket],
    path: str | Path,
) -> None:
    """Write human-review tickets to a CSV file."""
    ticket_by_id = {ticket.id: ticket for ticket in tickets}
    rows: list[dict[str, object]] = []
    for decision in decisions:
        if not decision.needs_review:
            continue
        ticket = ticket_by_id.get(decision.id)
        if ticket is None:
            continue
        rows.append(
            {
                "id": ticket.id,
                "customer": ticket.customer,
                "subject": ticket.subject,
                "body": (ticket.body or "")[:300],
                "review_reasons": "; ".join(decision.review_reasons),
                "suggested_category": (
                    decision.suggested_category.value
                    if decision.suggested_category is not None
                    else ""
                ),
                "suggested_priority": (
                    decision.suggested_priority.value
                    if decision.suggested_priority is not None
                    else ""
                ),
                "confidence": (
                    decision.confidence if decision.confidence is not None else ""
                ),
            }
        )

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        rows,
        columns=[
            "id",
            "customer",
            "subject",
            "body",
            "review_reasons",
            "suggested_category",
            "suggested_priority",
            "confidence",
        ],
    ).to_csv(output_path, index=False)
