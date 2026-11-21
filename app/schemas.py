"""Pydantic schemas for tickets and triage decisions."""

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class Category(str, Enum):
    """Allowed support ticket categories."""

    BILLING = "Billing"
    TECHNICAL = "Technical"
    ACCOUNT = "Account"
    SHIPPING = "Shipping"
    OTHER = "Other"


class Priority(str, Enum):
    """Allowed support ticket priorities."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"


class Ticket(BaseModel):
    """One support ticket from the input CSV."""

    id: str
    received_at: str
    customer: str
    subject: str
    body: Optional[str] = None


class LLMTriageResult(BaseModel):
    """Validated structured output returned by an LLM."""

    model_config = ConfigDict(extra="forbid")

    category: Category
    priority: Priority
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(max_length=200)


class TriageDecision(BaseModel):
    """Final routing and review decision for one ticket."""

    id: str
    category: Optional[Category] = None
    priority: Optional[Priority] = None
    needs_review: bool
    review_reasons: list[str]
    source: Literal["llm", "rule", "fallback"]
    suggested_category: Optional[Category] = None
    suggested_priority: Optional[Priority] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    latency_ms: int
    attempts: int
    error: Optional[str] = None
