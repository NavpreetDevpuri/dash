from typing import List, Optional
from pydantic import BaseModel, Field


class Identifiers(BaseModel):
    """Schema for extracted identifiers from WhatsApp messages."""
    identifiers: List[str] = Field(
        description="List of extracted identifiers from the message content"
    )


class AnalysisResult(BaseModel):
    """Schema for WhatsApp message analysis results."""
    spam_score: float = Field(
        description="The likelihood this message is spam (0.0 to 1.0)"
    )
    urgency_score: float = Field(
        description="How urgent/time-sensitive the message is (0.0 to 1.0)"
    )
    importance_score: float = Field(
        description="How important the message is for the recipient (0.0 to 1.0)"
    )
    summary: Optional[str] = Field(
        None, description="Optional brief summary of the message"
    ) 