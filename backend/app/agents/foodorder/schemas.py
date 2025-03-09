from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Rating(BaseModel):
    rating: Optional[float] = None
    votes: Optional[int] = None

class Dish(BaseModel):
    name: str
    desc: str
    rating: Optional[Rating] = None
    price: float
    tags: Optional[List[str]] = []
    item_image_filename: Optional[str] = None

class DishSchema(BaseModel):
    dishes: List[Dish]


