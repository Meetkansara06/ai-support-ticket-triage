# Overview

This project processes support tickets and sends each one to a category and priority decision. It also sends uncertain or risky tickets to a human review queue.

# Setup

Create a virtual environment and activate it. On Windows PowerShell, run `python -m venv .venv`, then `.venv\Scripts\Activate.ps1`. Install dependencies with `python -m pip install -r requirements.txt`.

Copy `.env.example` to `.env`. Set `LLM_PROVIDER`, `GEMINI_API_KEY` or `OPENAI_API_KEY`, and `MODEL_NAME` when using a real provider. Never commit the `.env` file.

# How to Run

Run `pytest -q` to run the tests. Run `python main.py` to process the default CSV with a real LLM. Run `python main.py --mock --limit 20` for a quick mock run.

The main outputs are `outputs/results.csv`, `outputs/review_queue.csv`, `outputs/details.csv`, and `outputs/run_report.json`.

# Architecture

- `app/preprocess.py` loads and prepares ticket text.
- `app/rules.py` checks insufficient content, prompt injection, and critical keywords.
- `app/classifier.py` validates and retries LLM classifications.
- `app/llm/` contains Gemini, OpenAI, and mock clients.
- `app/decision.py` combines rules and model results into the final decision.
- `app/pipeline.py` processes tickets concurrently.
- `app/review.py`, `app/metrics.py`, and `app/report.py` create review and run outputs.

Data flow: CSV -> preprocess -> rules -> LLM classifier with retry and validation -> decision engine -> results.csv / review_queue.csv -> run_report.json.

# Implemented vs Proposed

Implemented:

- CSV ticket loading and text preparation.
- Pydantic schemas and environment settings.
- Pure rules for review triggers.
- Gemini, OpenAI, and deterministic mock clients.
- JSON parsing, validation, retries, caching, and concurrent processing.
- results.csv, details.csv, review_queue.csv, and run_report.json.
- Unit tests using mock clients.

Proposed:

- Message queue and distributed workers.
- Shared cache.
- Monitoring and alerting.
- A Streamlit dashboard.
- Gold-sample evaluation with human-labelled tickets.

# Evaluation

The dataset has no ground-truth labels, so the project does not report accuracy.

The submitted results.csv was produced in mock mode. The mock client is a simple keyword-based stand-in, so its categories and priorities are not real Gemini output. The real Gemini run was not completed because of a model configuration error.

Mock-mode numbers from the 300-ticket run are: 300 total tickets, 267 automatically resolved, 33 sent to review, 294 LLM successes, 0 LLM failures, 0 fallbacks, 0 retries, 10 cache hits, 0.18666666666666668 average latency milliseconds, 0.0 p95 latency milliseconds, and 15331 estimated tokens. Mock review reasons are critical keywords, insufficient content, prompt-injection suspicion, and urgent priority review.

# Design Note

- For 50,000 tickets per day, use a message queue and several workers. Keep processing stateless and add backpressure before the LLM provider is overloaded.
- Use provider rate limits and exponential backoff. Retry only timeout, rate-limit, server, JSON, and validation failures.
- Cache by normalized text hash and keep the LLM client behind a small interface. This makes provider or mock changes easier.
- Send uncertain tickets to a human review queue. Reviewer corrections should become labelled data for later checks.
- To see whether it still works after a month, watch review rate, confidence, and failures over time. Check a small sample by hand every week and log the prompt and model version for each decision.
- Keep prompt-injection text and junk-ticket text inside the triage data. Rules should flag these tickets for review and should not let ticket text change categories or priorities directly.
