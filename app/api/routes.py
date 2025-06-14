from fastapi import APIRouter, HTTPException, Query

from app.database import get_db
from app.schemas import (MaqalListResponse, MaqalResponse, SearchResponse,
                         TopicMaqalResponse, TopicsResponse)
from app.utils import (create_maqal_from_row, create_pagination,
                       create_topic_from_row)

router = APIRouter()


@router.get("/", tags=["General"])
def read_root():
    return {"message": "Maqal-matel API жұмыс істеп тұр! 🇰🇿"}


@router.get("/random", response_model=MaqalResponse, tags=["Maqal"])
def get_random_maqal():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM maqal_matelder ORDER BY RANDOM() LIMIT 1")
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Мақал-мәтел табылмады(")

        return MaqalResponse(
            data=create_maqal_from_row(row), message="Random maqal retrieved"
        )


@router.get("/maqal-matel", response_model=MaqalListResponse, tags=["Maqal"])
def get_all_maqals(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
):
    """Get all maqal-matel with pagination"""
    offset = (page - 1) * limit

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM maqal_matelder")
        total = cursor.fetchone()[0]

        # Get paginated results
        cursor.execute(
            """
            SELECT * FROM maqal_matelder 
            ORDER BY id 
            LIMIT ? OFFSET ?
        """,
            (limit, offset),
        )

        rows = cursor.fetchall()
        results = [create_maqal_from_row(row) for row in rows]
        return MaqalListResponse(
            results=results,
            pagination=create_pagination(total, page, limit),
            message=f"Page {page} of {(total + limit - 1) // limit}",
        )


@router.get("/maqal-matel/{id}", response_model=MaqalResponse, tags=["Maqal"])
def get_maqal(id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM maqal_matelder WHERE id = ?", (id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Мақал-мәтел табылмады(")

        return MaqalResponse(
            data=create_maqal_from_row(row), message="Maqal retrieved successfully"
        )


@router.get("/search", response_model=SearchResponse, tags=["Maqal"])
def search_maqal(
    query: str = Query(..., min_length=1, description="Search query", alias="q"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
):
    """Search maqal-matel by text content with pagination"""
    offset = (page - 1) * limit
    search_term = f"%{query}%"

    with get_db() as conn:
        cursor = conn.cursor()

        # Find total number of maqal-matel
        cursor.execute(
            "SELECT COUNT(*) FROM maqal_matelder WHERE text LIKE ?", (search_term,)
        )
        total = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT * FROM maqal_matelder
            WHERE text LIKE ?
            ORDER BY id
            LIMIT ? OFFSET ?
                       """,
            (search_term, limit, offset),
        )

        rows = cursor.fetchall()

        results = [create_maqal_from_row(row) for row in rows]
        return SearchResponse(
            query=query,
            results=results,
            pagination=create_pagination(total, page, limit),
            message=f"Page {page} of {(total + limit - 1) // limit}",
        )


@router.get("/topics", response_model=TopicsResponse, tags=["Maqal"])
def get_all_topics():
    """Get all unique topics with counts"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT t.value as topic, COUNT(*) as count
            FROM maqal_matelder m, json_each(m.topics) t
            GROUP BY t.value
            ORDER BY count DESC, topic
        """
        )

        rows = cursor.fetchall()

        topics = [create_topic_from_row(row) for row in rows]
        return TopicsResponse(
            topics=topics,
            message="Topics retrieved successfully",
            total_topics=len(topics),
        )


@router.get("/topics/{topic}", response_model=TopicMaqalResponse, tags=["Maqal"])
def search_maqals_by_topic(
    topic: str,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
):
    """ "Get maqal-matels by specific topic"""
    offset = (page - 1) * limit

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT m.* FROM maqal_matelder m, json_each(m.topics) t
            WHERE t.value LIKE ?
            ORDER BY m.id
            LIMIT ?  
            """,
            (f"%{topic}%", limit),
        )

        rows = cursor.fetchall()

        results = [create_maqal_from_row(row) for row in rows]
        return TopicMaqalResponse(
            topic=topic,
            results=results,
            pagination=create_pagination(len(results), page, limit),
            message=f"Page {page} of {(len(results) + limit - 1) // limit}",
        )
