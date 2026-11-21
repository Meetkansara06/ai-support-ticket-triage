"""Ticket loading, text preparation, and cache-key generation."""

import hashlib
import re
from pathlib import Path

import pandas as pd

from app.schemas import Ticket


def load_tickets(path: str | Path) -> list[Ticket]:
    """Load tickets from a CSV file."""
    csv_path = Path(path)
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    try:
        frame = pd.read_csv(csv_path, dtype=str)
    except pd.errors.EmptyDataError as exc:
        raise ValueError(f"CSV file is empty: {csv_path}") from exc
    except pd.errors.ParserError as exc:
        raise ValueError(f"Bad CSV format in {csv_path}: {exc}") from exc

    required = {"id", "received_at", "customer", "subject", "body"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required CSV columns: {', '.join(sorted(missing))}")

    tickets: list[Ticket] = []
    for row in frame.to_dict(orient="records"):
        body = row.get("body")
        if pd.isna(body) or body is None:
            normalized_body = None
        else:
            normalized_body = str(body).strip() or None
        subject = "" if pd.isna(row.get("subject")) else str(row["subject"]).strip()
        tickets.append(
            Ticket(
                id=str(row["id"]).strip(),
                received_at="" if pd.isna(row.get("received_at")) else str(row["received_at"]).strip(),
                customer="" if pd.isna(row.get("customer")) else str(row["customer"]).strip(),
                subject=subject,
                body=normalized_body,
            )
        )
    return tickets


def prepare_text(ticket: Ticket, max_chars: int) -> str:
    """Prepare a bounded ticket text representation."""
    subject = (ticket.subject or "").strip()
    body = (ticket.body or "").strip()
    text = f"Subject: {subject} Body: {body}"
    if len(text) <= max_chars:
        return text

    marker = "[...truncated...]"
    budget = max(max_chars - len(marker), 0)
    head_chars = int(budget * 0.75)
    tail_chars = budget - head_chars
    return text[:head_chars] + marker + (text[-tail_chars:] if tail_chars else "")


def text_hash(ticket: Ticket) -> str:
    """Return a normalized SHA-256 cache key for a ticket."""
    subject = re.sub(r"\s+", " ", (ticket.subject or "").lower()).strip()
    body = re.sub(r"\s+", " ", (ticket.body or "").lower()).strip()
    normalized = f"{subject}\n{body}"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
