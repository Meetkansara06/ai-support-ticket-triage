"""Deterministic mock LLM client for tests and local runs."""

import json

from app.llm.base import LLMClient, LLMTimeoutError


class MockLLMClient(LLMClient):
    """Keyword-based mock supporting timeout, invalid JSON, and low confidence."""

    def __init__(
        self,
        *,
        timeout: bool = False,
        invalid_json: bool = False,
        low_confidence: bool = False,
    ) -> None:
        self.timeout = timeout
        self.invalid_json = invalid_json
        self.low_confidence = low_confidence

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        timeout_s: int,
    ) -> str:
        if self.timeout:
            raise LLMTimeoutError("mock timeout")
        if self.invalid_json:
            return "{invalid"

        text = user_prompt.lower()
        if any(term in text for term in ("refund", "invoice", "card", "payment", "bank transfer")):
            category = "Billing"
            priority = "High" if "wrong" in text or "charged" in text else "Medium"
        elif any(term in text for term in ("password", "login", "account", "2fa")):
            category = "Account"
            priority = "Medium"
        elif any(term in text for term in ("ship", "delivery", "order", "wrong item")):
            category = "Shipping"
            priority = "Medium"
        elif any(term in text for term in ("crash", "error", "bug", "down", "outage", "technical")):
            category = "Technical"
            priority = "Urgent" if "down" in text or "outage" in text else "High"
        else:
            category = "Other"
            priority = "Low"

        confidence = 0.4 if self.low_confidence else 0.92
        result = {
            "category": category,
            "priority": priority,
            "confidence": confidence,
            "reason": "Deterministic mock triage.",
        }
        return json.dumps(result)
