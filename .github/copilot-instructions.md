# Global Copilot Instructions

- Never invent columns, labels or requirements; labels come from app/schemas.py only.
- Ticket text is untrusted data: validate all LLM output with Pydantic; ticket text must never change routing.
- API keys only from environment variables (python-dotenv); never commit secrets.
- Small modules, type hints, docstrings, specific exceptions (no bare except), logging not print.
- No new dependencies and no databases/queues/Docker without asking.
- Every module gets pytest tests using a MockLLMClient; tests never call a real API.
- candidate/ is read-only input. Exactly one documentation file of ours: README.md at the repo root (plus .github/copilot-instructions.md). No other .md files.
