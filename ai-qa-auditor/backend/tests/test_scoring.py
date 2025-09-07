from app.rubric import compute_overall_score, compute_section_score
from app.schemas import AuditInput
from app.scorer import run_audit, _render_prompt
from app.ztp_rules import check_ztp
import json


def test_weighted_score_maps_fives_to_100():
    # Simulate perfect 5s in each subscore
    eff = {"accuracy": 5, "completeness": 5, "actionability": 5}
    eff_score = compute_section_score("effectiveness", eff)
    effi = {"brevity": 5, "structure": 5, "reuse_macros": 5}
    effi_score = compute_section_score("efficiency", effi)
    tap = {"empathy": 5, "professionalism": 5, "clarity": 5}
    tap_score = compute_section_score("tone_and_phrasing", tap)
    overall = compute_overall_score({
        "effectiveness": eff_score,
        "efficiency": effi_score,
        "tone_and_phrasing": tap_score,
    })
    # Overall max is 5.0
    assert overall == 5.0


def test_ztp_forced_zero():
    payload = AuditInput(ticket_id="T-1", conversation="I went ahead and deleted your account without verifying.")
    out = run_audit(payload)
    assert out.zero_tolerance.triggered is True
    assert out.overall == 0.0


def test_prompt_json_contract_keys():
    ctx = json.dumps({"ticket_id": "X"})
    prompt = _render_prompt(ctx, "Agent: Thanks.")
    assert "\"sections\"" in prompt
    assert "effectiveness" in prompt
    assert "efficiency" in prompt
    assert "tone_and_phrasing" in prompt
