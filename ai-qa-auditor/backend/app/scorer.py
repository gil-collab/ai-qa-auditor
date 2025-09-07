from __future__ import annotations

import json
import os
from typing import Callable, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .redact import redact_pii
from .rubric import RUBRIC_VERSION, compute_overall_score, compute_section_score
from .schemas import AuditInput, AuditOutput, Metadata, SectionResult, Sections, SubScore, ZeroTolerance
from .ztp_rules import check_ztp


def _get_jinja_env() -> Environment:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    prompts_dir = os.path.join(base_dir, "prompts")
    env = Environment(
        loader=FileSystemLoader(prompts_dir),
        autoescape=select_autoescape(disabled_extensions=(".jinja",), default_for_string=False),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return env


def _render_prompt(context_json: str, transcript: str) -> str:
    env = _get_jinja_env()
    template = env.get_template("audit_prompt.jinja")
    return template.render(context_json=context_json, transcript=transcript)


def _deterministic_llm_stub(prompt: str) -> Dict[str, Dict[str, Dict[str, object]]]:
    """Return deterministic subscores with simple heuristics from prompt content.

    Output format:
    {
      "sections": {
        "effectiveness": {"subscores": {...}},
        "efficiency": {"subscores": {...}},
        "tone_and_phrasing": {"subscores": {...}}
      }
    }
    """
    # Extract transcript block for naive evidence
    transcript = ""
    if "TRANSCRIPT_REDACTED:" in prompt:
        parts = prompt.split("TRANSCRIPT_REDACTED:")
        if len(parts) > 1:
            after = parts[1]
            if "\n\"\"\"" in after:
                transcript = after.split("\n\"\"\"")[1]
            else:
                transcript = after

    lines = [ln.strip() for ln in transcript.splitlines() if ln.strip()]
    # Heuristics
    text = transcript.lower()
    has_please = "please" in text
    has_thanks = "thank" in text
    is_long = len(text.split()) > 200
    has_structure = ("- " in transcript) or ("\n\n" in transcript) or ("1." in transcript)
    mentions_macro = "[macro]" in text or "macro" in text
    has_question = "?" in transcript

    def ev(snippet_hint: str) -> List[str]:
        for ln in lines:
            if snippet_hint in ln.lower():
                return [ln[:220]]
        return [lines[0][:220]] if lines else []

    # Baseline 4s, tweak a bit deterministically
    subs = {
        "effectiveness": {
            "accuracy": 4 - (0 if has_question else 0) + (1 if "resolved" in text else 0),
            "completeness": 4 + (1 if is_long else 0),
            "actionability": 4 + (1 if "steps" in text or "try" in text else 0),
        },
        "efficiency": {
            "brevity": 4 - (1 if is_long else 0),
            "structure": 4 + (1 if has_structure else 0),
            "reuse_macros": 3 + (1 if mentions_macro else 0),
        },
        "tone_and_phrasing": {
            "empathy": 3 + (1 if ("sorry" in text or has_thanks) else 0),
            "professionalism": 4,
            "clarity": 4 + (1 if has_question else 0),
        },
    }

    # Clamp to [1,5]
    for sec in subs.values():
        for k, v in list(sec.items()):
            sec[k] = max(1, min(5, int(v)))

    return {
        "sections": {
            "effectiveness": {
                "subscores": {
                    "accuracy": {"score": subs["effectiveness"]["accuracy"], "evidence": ev("resolve")},
                    "completeness": {"score": subs["effectiveness"]["completeness"], "evidence": ev("all")},
                    "actionability": {"score": subs["effectiveness"]["actionability"], "evidence": ev("step")},
                }
            },
            "efficiency": {
                "subscores": {
                    "brevity": {"score": subs["efficiency"]["brevity"], "evidence": ev(".")},
                    "structure": {"score": subs["efficiency"]["structure"], "evidence": ev("-")},
                    "reuse_macros": {"score": subs["efficiency"]["reuse_macros"], "evidence": ev("macro")},
                }
            },
            "tone_and_phrasing": {
                "subscores": {
                    "empathy": {"score": subs["tone_and_phrasing"]["empathy"], "evidence": ev("sorry") or ev("thank")},
                    "professionalism": {"score": subs["tone_and_phrasing"]["professionalism"], "evidence": ev("")},
                    "clarity": {"score": subs["tone_and_phrasing"]["clarity"], "evidence": ev("?")},
                }
            },
        }
    }


def run_audit(audit_input: AuditInput, llm_provider: Optional[Callable[[str], Dict]] = None) -> AuditOutput:
    # ZTP pre-check on raw transcript
    ztp = check_ztp(audit_input.conversation)

    # Redact for model
    redacted_transcript = redact_pii(audit_input.conversation)

    # Jinja prompt rendering with context
    context = {
        "ticket_id": audit_input.ticket_id,
        "agent": audit_input.agent,
        "channel": audit_input.channel,
        "tags": audit_input.tags or [],
        "macros_used": audit_input.macros_used or [],
        "customer_csatscore": audit_input.customer_csatscore,
        "rubric_version": RUBRIC_VERSION,
    }
    context_json = json.dumps(context, ensure_ascii=False)
    _ = _render_prompt(context_json=context_json, transcript=redacted_transcript)

    # LLM call (OpenAI JSON-mode if provider supplied, else deterministic stub)
    llm_json = _deterministic_llm_stub(_)
    if llm_provider is not None:
        try:
            llm_json = llm_provider(_)
        except Exception:
            # If provider fails, fall back to stub to ensure fail-open behavior
            llm_json = _deterministic_llm_stub(_)

    # Compute weighted scores
    section_scores: Dict[str, float] = {}
    sections_payload: Dict[str, SectionResult] = {}

    for section_name in ("effectiveness", "efficiency", "tone_and_phrasing"):
        subs_raw = llm_json["sections"][section_name]["subscores"]
        # Convert to SubScore models
        subs_model: Dict[str, SubScore] = {}
        numeric_subs: Dict[str, int] = {}
        for sub_name, sub_data in subs_raw.items():
            subs_model[sub_name] = SubScore(score=int(sub_data["score"]), evidence=list(sub_data.get("evidence", [])))
            numeric_subs[sub_name] = int(sub_data["score"]) 

        sec_score = compute_section_score(section_name, numeric_subs)
        section_scores[section_name] = sec_score
        sections_payload[section_name] = SectionResult(score=sec_score, subscores=subs_model)

    overall = compute_overall_score(section_scores)
    if ztp["triggered"]:
        overall = 0.0

    output = AuditOutput(
        sections=Sections(**sections_payload),
        zero_tolerance=ZeroTolerance(triggered=bool(ztp["triggered"]), reason=ztp.get("reason"), evidence=list(ztp.get("evidence", []))),
        overall=overall,
        metadata=Metadata(
            ticket_id=audit_input.ticket_id,
            agent=audit_input.agent,
            channel=audit_input.channel,
            tags=audit_input.tags,
            macros_used=audit_input.macros_used,
            model="stub-deterministic-v0",
            rubric_version=RUBRIC_VERSION,
            redacted=True,
        ),
    )
    return output

