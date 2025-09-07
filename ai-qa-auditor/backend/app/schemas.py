from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, NonNegativeFloat, PositiveInt


class AuditInput(BaseModel):
    ticket_id: str = Field(..., description="Unique identifier for the ticket or conversation thread")
    agent: Optional[str] = Field(None, description="Agent identifier or name handling the conversation")
    channel: Optional[str] = Field(None, description="Support channel, e.g., email, chat, phone")
    conversation: str = Field(..., description="Full conversation transcript as plain text")
    macros_used: Optional[List[str]] = Field(default=None, description="List of macros used by the agent, if any")
    tags: Optional[List[str]] = Field(default=None, description="Optional tags present on the ticket")
    customer_csatscore: Optional[int] = Field(default=None, description="Customer CSAT score if provided (e.g., 1–5)")


class SubScore(BaseModel):
    score: PositiveInt = Field(..., ge=1, le=5, description="Sub-score on a 1–5 scale")
    evidence: List[str] = Field(default_factory=list, description="Quoted snippets or short rationale supporting the sub-score")


class SectionResult(BaseModel):
    score: NonNegativeFloat = Field(..., description="Weighted section score on a 0–5 scale")
    subscores: Dict[str, SubScore] = Field(..., description="Breakdown of sub-scores within the section")


class Sections(BaseModel):
    effectiveness: SectionResult
    efficiency: SectionResult
    tone_and_phrasing: SectionResult


class ZeroTolerance(BaseModel):
    triggered: bool
    reason: Optional[str] = None
    evidence: List[str] = Field(default_factory=list)


class Metadata(BaseModel):
    ticket_id: str
    agent: Optional[str] = None
    channel: Optional[str] = None
    tags: Optional[List[str]] = None
    macros_used: Optional[List[str]] = None
    model: str = Field(..., description="Model identifier used for scoring")
    rubric_version: str = Field(..., description="Version string of the rubric used for scoring")
    redacted: bool = Field(default=True, description="Whether PII was redacted before model evaluation")


class AuditOutput(BaseModel):
    sections: Sections
    zero_tolerance: ZeroTolerance
    overall: NonNegativeFloat = Field(..., description="Overall weighted score on a 0–5 scale (0 if ZTP triggered)")
    metadata: Metadata

