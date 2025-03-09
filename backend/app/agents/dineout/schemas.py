from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Restaurant(BaseModel):
    """Restaurant information schema"""
    id: str = Field(description="Unique identifier for the restaurant")
    name: str = Field(description="Name of the restaurant")
    cuisine: List[str] = Field(description="Types of cuisine served", default_factory=list)
    price_range: str = Field(description="Price range indicator (e.g., $, $$, $$$)")
    rating: float = Field(description="Average rating (1-5 scale)")
    location: str = Field(description="Location/address of the restaurant")
    opening_hours: Dict[str, str] = Field(description="Opening hours by day of week", default_factory=dict)
    phone: Optional[str] = Field(None, description="Contact phone number")
    website: Optional[str] = Field(None, description="Restaurant website")


class SearchResult(BaseModel):
    """Search results with restaurant information"""
    restaurants: List[Restaurant] = Field(description="List of restaurants matching search criteria")
    query: str = Field(description="Original search query")
    total_count: int = Field(description="Total number of matching restaurants") 