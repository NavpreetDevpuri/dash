from typing import List, Optional
from pydantic import BaseModel, Field


class Identifiers(BaseModel):
    """Used to get identifiers from the text content"""
    identifiers: List[str] = Field(description="List of identifiers found in the text content")


class AnalysisResult(BaseModel):
    """Used to get analysis results from the text content"""
    is_spam: bool = Field(..., description="Whether the message appears to be spam")
    is_urgent: bool = Field(..., description="Whether the message appears to be urgent")
    is_important: bool = Field(..., description="Whether the message appears to be important")
    spam_score: float = Field(..., description="Confidence score for spam detection (0-1)")
    urgency_score: float = Field(..., description="Confidence score for urgency (0-1)")
    importance_score: float = Field(..., description="Confidence score for importance (0-1)")
    reason: str = Field(description="Reason for the analysis results")


