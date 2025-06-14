from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Maqal(BaseModel):
    id: int
    text: str = Field(..., description="Maqal-matel text")
    topics: List[str] = Field(..., description="List of topics")
    created_at: datetime

    class Config:
        from_attributes = True


class MaqalResponse(BaseModel):
    success: bool = True
    data: Maqal
    message: str


class MaqalListResponse(BaseModel):
    success: bool = True
    results: List[Maqal]
    pagination: Optional["PaginationInfo"] = None
    message: str


class PaginationInfo(BaseModel):
    total_items: int
    current_page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_previous: bool


class SearchResponse(BaseModel):
    success: bool = True
    query: str
    results: List[Maqal]
    pagination: Optional[PaginationInfo] = None
    message: str


class TopicInfo(BaseModel):
    topic: str
    count: int


class TopicsResponse(BaseModel):
    success: bool = True
    topics: List[TopicInfo]
    total_topics: int
    message: str


class TopicMaqalResponse(BaseModel):
    """Topic-specific maqal-matelder response"""

    success: bool = True
    topic: str
    results: List[Maqal]
    pagination: Optional[PaginationInfo] = None
    message: str


MaqalListResponse.model_rebuild()
SearchResponse.model_rebuild()
TopicMaqalResponse.model_rebuild()
