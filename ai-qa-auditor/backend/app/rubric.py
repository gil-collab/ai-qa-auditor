from __future__ import annotations

from typing import Dict


RUBRIC_VERSION = "1.0.0"


# Section weights must sum to 1.0
SECTION_WEIGHTS: Dict[str, float] = {
    "effectiveness": 0.4,
    "efficiency": 0.3,
    "tone_and_phrasing": 0.3,
}


# Subscore weights within each section must sum to 1.0
SUBSCORE_WEIGHTS: Dict[str, Dict[str, float]] = {
    "effectiveness": {
        "accuracy": 0.5,
        "completeness": 0.3,
        "actionability": 0.2,
    },
    "efficiency": {
        "brevity": 0.4,
        "structure": 0.3,
        "reuse_macros": 0.3,
    },
    "tone_and_phrasing": {
        "empathy": 0.4,
        "professionalism": 0.3,
        "clarity": 0.3,
    },
}


def compute_section_score(section_name: str, subscores: Dict[str, int]) -> float:
    weights = SUBSCORE_WEIGHTS[section_name]
    weighted_total = 0.0
    for sub_name, weight in weights.items():
        score = float(subscores.get(sub_name, 3))
        weighted_total += weight * score
    return round(weighted_total, 3)


def compute_overall_score(section_scores: Dict[str, float]) -> float:
    weighted_total = 0.0
    for section_name, section_weight in SECTION_WEIGHTS.items():
        weighted_total += section_weight * float(section_scores.get(section_name, 0.0))
    return round(weighted_total, 3)

