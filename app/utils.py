import json
from datetime import datetime

from app.models import Maqal, PaginationInfo, TopicInfo


def create_maqal_from_row(row) -> Maqal:
    """Helper function to convert database row to Maqal model"""
    created_at = row["created_at"]

    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

    # We need to prevent nested JSON object.
    # Because it weirdly fethches maqal-matels, so we need to properly encode it
    topics_data = row["topics"]
    try:
        topics = json.loads(topics_data)
        if isinstance(topics, dict) and "topics" in topics:
            topics = topics["topics"]

        # Ensure it's a list
        if not isinstance(topics, list):
            topics = []
    except (json.JSONDecodeError, TypeError):
        topics = []

    return Maqal(id=row["id"], text=row["text"], topics=topics, created_at=created_at)


def create_pagination(total: int, page: int, limit: int) -> PaginationInfo:
    """Helper function to create pagination info"""
    return PaginationInfo(
        total_items=total,
        current_page=page,
        per_page=limit,
        total_pages=(total + limit - 1) // limit,
        has_next=page * limit < total,
        has_previous=page > 1,
    )


def create_topic_from_row(row) -> TopicInfo:
    """Helper function to convert database row to TopicInfo model"""
    return TopicInfo(count=row["count"], topic=row["topic"])


def paginated_response(
    results: list,
    total: int,
    page: int,
    limit: int,
    message: str,
):
    """Helper function for consistent pagination"""
    return {
        "results": results,
        "pagination": {
            "total_items": total,
            "current_page": page,
            "per_page": limit,
            "total_pages": (total + limit - 1) // limit,
            "has_next": page * limit < total,
            "has_previous": page > 1,
        },
        "message": message,
    }
