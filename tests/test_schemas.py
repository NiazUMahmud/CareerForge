import pytest
from pydantic import ValidationError

from careerforge.schemas import CompanyResearch, InterviewPrepKit


def test_company_research_minimal():
    result = CompanyResearch(
        company_name="Acme Inc.",
        summary="A payments company.",
        confidence=0.8,
    )
    assert result.culture_notes == []
    assert result.confidence == 0.8


def test_company_research_confidence_out_of_range_rejected():
    with pytest.raises(ValidationError):
        CompanyResearch(company_name="Acme", summary="x", confidence=1.5)


def test_interview_prep_kit_requires_lists():
    kit = InterviewPrepKit(
        likely_questions=["Tell me about yourself"],
        suggested_talking_points=["STAR point"],
        questions_to_ask_interviewer=["What's the team's biggest challenge?"],
        confidence=0.6,
    )
    assert len(kit.likely_questions) == 1
