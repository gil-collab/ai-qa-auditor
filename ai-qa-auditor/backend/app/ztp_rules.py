from __future__ import annotations

import re
from typing import Dict, List, Tuple


# Zero Tolerance Patterns (conservative)

# 1) Deletion without permission (phrases strongly implying unilateral destructive action)
DELETION_PATTERNS = [
    r"\bwent ahead and (?:deleted|removed|wiped|erased)\b",
    r"\bdeleted (?:your|the) (?:account|data|file|files|message|messages|ticket)\b",
    r"\bremoved (?:your|the) (?:account|data|file|files|message|messages|ticket)\b",
]

# 2) Verification skipped (explicitly stating absence of verification)
VERIFICATION_PATTERNS = [
    r"\bskipp?ed (?:id|identity|verification)\b",
    r"\bno need to (?:verify|confirm)\b",
    r"\bwithout (?:verifying|confirming)\b",
    r"\bcouldn't verify (?:you|identity) but (?:proceeded|went ahead)\b",
]

# 3) Privacy/off-platform or asking for sensitive info
PRIVACY_PATTERNS = [
    r"\bDM me\b",
    r"\btext me\b",
    r"\bWhatsApp\b",
    r"\bTelegram\b",
    r"\bpersonal email\b",
    r"\boff[- ]platform\b",
    r"\boutside (?:this|the) platform\b",
    r"\bshare your (?:password|passcode|SSN|social security|credit card)\b",
]


COMPILED_RULES: List[Tuple[str, List[re.Pattern]]] = [
    ("deletion_without_permission", [re.compile(p, re.IGNORECASE) for p in DELETION_PATTERNS]),
    ("verification_skipped", [re.compile(p, re.IGNORECASE) for p in VERIFICATION_PATTERNS]),
    ("privacy_off_platform", [re.compile(p, re.IGNORECASE) for p in PRIVACY_PATTERNS]),
]


def check_ztp(text: str) -> Dict[str, object]:
    """Check Zero Tolerance Policy rules on raw transcript.

    Returns a dict with:
      - triggered: bool
      - reason: str | None
      - evidence: List[str]
    """
    evidence: List[str] = []
    reason: str | None = None

    if not text:
        return {"triggered": False, "reason": None, "evidence": []}

    for rule_name, patterns in COMPILED_RULES:
        for pat in patterns:
            for m in pat.finditer(text):
                snippet = _extract_snippet(text, m.start(), m.end())
                evidence.append(snippet)
                # First match determines reason for clarity
                if reason is None:
                    reason = rule_name
        if evidence and reason:
            return {"triggered": True, "reason": reason, "evidence": evidence}

    return {"triggered": False, "reason": None, "evidence": []}


def _extract_snippet(text: str, start: int, end: int, window: int = 60) -> str:
    a = max(0, start - window)
    b = min(len(text), end + window)
    snippet = text[a:b].strip()
    return snippet

