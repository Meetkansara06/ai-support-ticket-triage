"""Pure rule-based escalation decisions."""

import re
from dataclasses import dataclass

from app.schemas import Ticket


@dataclass(frozen=True)
class RuleResult:
    """Flags derived from ticket content."""

    flags: list[str]
    skip_llm: bool


JUNK_PATTERNS = (
    "sent from my phone",
    "asdf",
    "test test",
)

INJECTION_PATTERNS = (
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"system\s+note",
    r"note\s+to\s+(the\s+)?ai",
    r"assistant\s*:",
    r"do\s+not\s+send\s+.+\s+for\s+review",
    r"output\s+priority",
    r"the\s+rules\s+have\s+changed",
    r"classify\s+this\s+ticket\s+as",
)

CRITICAL_PATTERNS = (
    r"hacked",
    r"unauthori[sz]ed",
    r"fraud",
    r"did\s+not\s+(make|do\s+it)",
    r"breach",
    r"solicitor",
    r"ombudsman",
    r"lawyer",
    r"\blegal\b",
    r"whole\s+office",
    r"all\s+our\s+devices",
    r"service\s+down",
    r"перехвач",  # hijacked
    r"hackeado",
    r"gegevenslek",
)


def apply_rules(ticket: Ticket) -> RuleResult:
    """Derive review flags without changing category or priority."""
    flags: list[str] = []
    subject = ticket.subject or ""
    body = ticket.body or ""
    combined = f"{subject}\n{body}"

    combined_lower = combined.lower()
    body_words = re.findall(r"\b[\w'-]+\b", body, flags=re.UNICODE)
    junk = any(pattern in combined_lower for pattern in JUNK_PATTERNS)
    if not body.strip() or len(body_words) < 3 or junk:
        flags.append("insufficient_content")

    if any(re.search(pattern, combined_lower, re.IGNORECASE) for pattern in INJECTION_PATTERNS):
        flags.append("prompt_injection_suspected")

    for pattern in CRITICAL_PATTERNS:
        if re.search(pattern, combined_lower, re.IGNORECASE):
            keyword = pattern.replace(r"\b", "")
            flags.append(f"critical_keyword:{keyword}")

    skip_llm = "insufficient_content" in flags or "prompt_injection_suspected" in flags
    return RuleResult(flags=flags, skip_llm=skip_llm)
