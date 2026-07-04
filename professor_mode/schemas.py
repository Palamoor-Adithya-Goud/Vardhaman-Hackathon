"""
Strict JSON Pydantic Schemas for the Professor Intelligence Layer.
Enforces validation matching project specifications.
"""

from typing import List, Literal
from pydantic import BaseModel, Field

class TrendItem(BaseModel):
    title: str = Field(description="Title of the research trend or paper")
    summary: str = Field(description="Summary of the trend findings")
    source: Literal["tavily", "arxiv"] = Field(description="The source of the intelligence")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0", ge=0.0, le=1.0)

class TrendAnalysisOutput(BaseModel):
    topic: str = Field(description="The input topic analyzed")
    trends: List[TrendItem] = Field(description="List of trends identified")
    emerging_areas: List[str] = Field(description="List of emerging sub-topics or areas")

class OpportunityGap(BaseModel):
    gap: str = Field(description="The identified research gap")
    why_it_matters: str = Field(description="Detailed explanation of why this gap is important to fill")

class GapAnalysisOutput(BaseModel):
    covered_areas: List[str] = Field(description="Research areas currently covered by the faculty")
    missing_areas: List[str] = Field(description="Research areas missing from the faculty's expertise")
    opportunity_gaps: List[OpportunityGap] = Field(description="Opportunities and gaps identified")

class ProjectSuggestion(BaseModel):
    title: str = Field(description="Proposed project title")
    description: str = Field(description="Proposed project description and scope")
    faculty: List[str] = Field(description="Grounded faculty member names suggested for this project")
    trend_alignment: str = Field(description="How this project aligns with identified trends")
    gap_alignment: str = Field(description="How this project addresses identified gaps")
    impact: str = Field(description="Anticipated research impact of this project")

class ProjectSuggestionOutput(BaseModel):
    projects: List[ProjectSuggestion] = Field(description="List of suggested research projects")

class EmailDraft(BaseModel):
    subject: str = Field(description="Professional email subject")
    body: str = Field(description="Professional email body content")
