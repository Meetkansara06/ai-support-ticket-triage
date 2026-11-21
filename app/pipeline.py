"""Batch processing and controlled ticket concurrency."""

from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import time
from threading import Lock

from app.classifier import TriageError, classify
from app.config import Settings
from app.decision import decide
from app.llm.base import LLMClient
from app.preprocess import prepare_text
from app.rules import apply_rules
from app.schemas import LLMTriageResult, Ticket, TriageDecision


LOGGER = logging.getLogger(__name__)


class PipelineDecisions(list[TriageDecision]):
    """Ordered decisions with aggregate run statistics."""

    def __init__(self) -> None:
        super().__init__()
        self.retries = 0
        self.cache_hits = 0
        self.estimated_tokens = 0
        self.llm_successes = 0
        self.llm_failures = 0


def run_pipeline(
    tickets: list[Ticket],
    client: LLMClient,
    settings: Settings,
) -> PipelineDecisions:
    """Process tickets concurrently and return decisions in input order."""
    cache: dict[str, LLMTriageResult] = {}
    stats_lock = Lock()
    decisions: dict[int, TriageDecision] = {}
    results = PipelineDecisions()

    def process(ticket: Ticket) -> TriageDecision:
        started = time.perf_counter()
        attempts = 0
        llm_result: LLMTriageResult | None = None
        error: str | None = None
        rule_result = apply_rules(ticket)

        try:
            if not rule_result.skip_llm:
                llm_result, attempts, from_cache = classify(
                    ticket, client, settings, cache
                )
                with stats_lock:
                    if from_cache:
                        results.cache_hits += 1
                    else:
                        results.llm_successes += 1
                    if attempts > 1:
                        results.retries += attempts - 1
        except TriageError as exc:
            error = str(exc)
            LOGGER.warning("Ticket %s fell back after classification failure", ticket.id)
            with stats_lock:
                results.llm_failures += 1
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            LOGGER.warning("Ticket %s fell back after unexpected failure", ticket.id)
            with stats_lock:
                results.llm_failures += 1

        latency_ms = int((time.perf_counter() - started) * 1000)
        text = prepare_text(ticket, settings.MAX_BODY_CHARS)
        with stats_lock:
            results.estimated_tokens += int(len(text) / 4)

        return decide(
            ticket,
            rule_result,
            llm_result,
            error,
            confidence_threshold=settings.CONFIDENCE_THRESHOLD,
            latency_ms=latency_ms,
            attempts=attempts,
        )

    with ThreadPoolExecutor(max_workers=settings.CONCURRENCY) as executor:
        futures = {
            executor.submit(process, ticket): index
            for index, ticket in enumerate(tickets)
        }
        for future in as_completed(futures):
            index = futures[future]
            try:
                decisions[index] = future.result()
            except Exception as exc:
                LOGGER.exception("Unexpected pipeline failure for ticket index %s", index)
                ticket = tickets[index]
                decisions[index] = decide(
                    ticket,
                    apply_rules(ticket),
                    None,
                    f"{type(exc).__name__}: {exc}",
                    confidence_threshold=settings.CONFIDENCE_THRESHOLD,
                    latency_ms=0,
                    attempts=0,
                )

    results.extend(decisions[index] for index in range(len(tickets)))
    return results
