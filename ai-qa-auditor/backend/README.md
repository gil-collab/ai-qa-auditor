# AI QA Auditor – Backend

Minimal FastAPI app that exposes POST /audit to return deterministic QA scores. Uses Pydantic v2 and a stubbed LLM for local development.

## Quickstart

1. Create virtualenv (optional) and install deps:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2. Run server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. Test:

```bash
curl -s -X POST http://localhost:8000/audit \
  -H 'content-type: application/json' \
  -d '{
    "ticket_id": "T-123",
    "channel": "email",
    "conversation": "Customer: Hello. Agent: Thanks for reaching out. Please try restarting."
  }' | jq .
```

## Project Structure

- `app/schemas.py`: Pydantic models for input/output
- `app/redact.py`: Redaction utilities for emails, phones, and links
- `app/ztp_rules.py`: Zero Tolerance checks with conservative regexes
- `app/rubric.py`: Section/subscore weights and score computation
- `app/prompts/audit_prompt.jinja`: Strict JSON prompt template
- `app/scorer.py`: Orchestrates ZTP, prompt render, stub LLM, and scoring
- `app/main.py`: FastAPI app exposing `/audit`

## Notes

- Zero Tolerance triggers set `overall` to 0.
- Evidence snippets are short quotes pulled from the transcript.
- Replace the stub in `scorer.py` with a real LLM client later; keep the prompt contract identical.
