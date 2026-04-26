from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class GroupBy(str, Enum):
    date = "date"
    offer = "offer"


class LeadIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=5, max_length=32)
    country: str = Field(pattern=r"^[A-Z]{2}$")
    offer_id: int
    affiliate_id: int


class LeadOut(BaseModel):
    id: int
    name: str
    phone: str
    country: str
    offer_id: int
    affiliate_id: int
    created_at: datetime
