from typing import List, Optional
from pydantic import BaseModel, Field


class Identifiers(BaseModel):
    """Used to get identifiers from the email content"""
    identifiers: List[str] = Field(description="List of identifiers found in the email content")


class AnalysisResult(BaseModel):
    """Used to get analysis results from the email content"""
    spam_score: float = Field(..., description="Confidence score for spam detection (0-1)")
    urgency_score: float = Field(..., description="Confidence score for urgency (0-1)")
    importance_score: float = Field(..., description="Confidence score for importance (0-1)")
    category: str = Field(description="Category of the email (e.g., personal, work, promotional, etc.)")
    reason: str = Field(description="Reason for the analysis results") 