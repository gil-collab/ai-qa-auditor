from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Dict

from fastapi import FastAPI, HTTPException

from .schemas import AuditInput, AuditOutput
from .scorer import run_audit

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

logger = logging.getLogger("ai-qa-auditor")
logging.basicConfig(level=logging.INFO)


app = FastAPI(title="AI QA Auditor", version="0.1.0")


@app.get("/")
def health() -> dict:
    return {"status": "ok"}


def _validate_llm_json(data: Dict) -> Dict:
    if not isinstance(data, dict) or "sections" not in data:
        raise ValueError("Invalid JSON from model: missing 'sections'")
    return data


def call_model(prompt: str) -> Dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY is not set")
    if OpenAI is None:
        raise HTTPException(status_code=400, detail="openai package not installed")
    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You output strict JSON only."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        content = resp.choices[0].message.content or "{}"
        data = json.loads(content)
        return _validate_llm_json(data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OpenAI error or invalid JSON: {e}")


async def _maybe_upsert_to_db(audit: AuditOutput) -> None:
    dsn = os.getenv("DB_DSN")
    if not dsn:
        return
    try:
        import asyncpg  # type: ignore
    except Exception:
        logger.error("asyncpg not installed; skipping DB upsert")
        return
    try:
        conn = await asyncpg.connect(dsn=dsn)
        try:
            await conn.execute(
                """
                insert into audits (
                  ticket_id, agent, channel, overall,
                  effectiveness, efficiency, tone_and_phrasing, zero_tolerance
                ) values ($1,$2,$3,$4,$5::jsonb,$6::jsonb,$7::jsonb,$8::jsonb)
                on conflict (ticket_id) do update set
                  agent = excluded.agent,
                  channel = excluded.channel,
                  overall = excluded.overall,
                  effectiveness = excluded.effectiveness,
                  efficiency = excluded.efficiency,
                  tone_and_phrasing = excluded.tone_and_phrasing,
                  zero_tolerance = excluded.zero_tolerance
                """,
                audit.metadata.ticket_id,
                audit.metadata.agent,
                audit.metadata.channel,
                audit.overall,
                json.dumps(audit.sections.effectiveness.model_dump()),
                json.dumps(audit.sections.efficiency.model_dump()),
                json.dumps(audit.sections.tone_and_phrasing.model_dump()),
                json.dumps(audit.zero_tolerance.model_dump()),
            )
        finally:
            await conn.close()
    except Exception as e:  # fail-open: log, don't raise
        logger.error("DB upsert failed: %s", e)


@app.post("/audit", response_model=AuditOutput)
async def audit(payload: AuditInput) -> AuditOutput:
    # Pass OpenAI call_model to scorer if API key is present; otherwise use stub
    provider = call_model if os.getenv("OPENAI_API_KEY") else None
    result = run_audit(payload, llm_provider=provider)
    # If run_audit cannot accept provider, we keep stub; alternatively adjust scorer to accept provider
    try:
        await _maybe_upsert_to_db(result)
    except Exception:
        pass
    return result

