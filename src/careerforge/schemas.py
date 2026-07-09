"""Structured-output schemas returned by CareerForge's subagents.

Using Pydantic ``response_format`` on subagents (a deepagents feature) means
the interview-coach and company-researcher subagents don't just hand back
free text — they return validated, typed objects the UI can render reliably
(no fragile markdown-parsing).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CompanyResearch(BaseModel):
    """Structured findings about a target company from the company-researcher subagent."""

    company_name: str = Field(description="Name of the company researched")
    summary: str = Field(description="2-4 sentence overview of the company")
    culture_notes: list[str] = Field(
        default_factory=list, description="Notable culture/values signals found"
    )
    recent_news: list[str] = Field(
        default_factory=list, description="Recent, relevant news headlines or events"
    )
    talking_points: list[str] = Field(
        default_factory=list,
        description="Specific facts the candidate can reference in a cover letter or interview",
    )
    sources: list[str] = Field(default_factory=list, description="Source URLs used")
    confidence: float = Field(description="Confidence score from 0 to 1", ge=0, le=1)


class InterviewPrepKit(BaseModel):
    """Structured interview prep produced by the interview-coach subagent."""

    likely_questions: list[str] = Field(
        description="Behavioral, technical, and company-specific questions likely to be asked"
    )
    suggested_talking_points: list[str] = Field(
        description="STAR-style talking points tying the candidate's resume to the role"
    )
    questions_to_ask_interviewer: list[str] = Field(
        description="Thoughtful questions the candidate should ask back"
    )
    confidence: float = Field(description="Confidence score from 0 to 1", ge=0, le=1)
