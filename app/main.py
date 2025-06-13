from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from app.database import init_db, get_db
from app.utils import paginated_response
import json

app = FastAPI(title="Maqal-matel API")


with open("data/maqal_matel_data.json", "r", encoding="utf-8") as file:
    data = json.load(file)


# Initialize db on startup
@app.on_event("startup")
async def startup_event():
    init_db()


@app.get("/")
def read_root():
    return {"message": "Maqal-matel API жұмыс істеп тұр! 🇰🇿"}


@app.get("/random")
def get_random_maqal():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM maqal_matelder ORDER BY RANDOM() LIMIT 1")
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Мақал-мәтел табылмады(")

        return {
            "id": row["id"],
            "text": row["text"],
            "topics": json.loads(row["topics"]),
            "created_at": row["created_at"],
        }


@app.get("/maqal-matel")
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

        results = []
        for row in rows:
            results.append(
                {
                    "id": row["id"],
                    "text": row["text"],
                    "topics": json.loads(row["topics"]),
                    "created_at": row["created_at"],
                }
            )

        return paginated_response(
            results,
            total,
            page,
            limit,
            f"Page {page} of {(total + limit - 1) // limit}",
        )


@app.get("/maqal-matel/{id}")
def get_maqal(id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM maqal_matelder WHERE id = ?", (id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Мақал-мәтел табылмады(")

        return {
            "id": row["id"],
            "text": row["text"],
            "topics": json.loads(row["topics"]),
            "created_at": row["created_at"],
        }


@app.get("/search")
def search_maqal(
    query: str = Query(..., min_length=1, description="Search query", alias="q"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
):
    """Search maqal-matel by text content with pagination"""
    with get_db() as conn:
        cursor = conn.cursor()

        offset = (page - 1) * limit
        search_term = f"%{query}%"

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

        results = []
        for row in rows:
            results.append(
                {
                    "id": row["id"],
                    "text": row["text"],
                    "topics": json.loads(row["topics"]),
                    "created_at": row["created_at"],
                }
            )

        return {
            "query": query,
            **paginated_response(
                results, total, page, limit, f"Search results for '{query}'"
            ),
        }


@app.get("/topics")
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

        topics = []
        for row in rows:
            topics.append({"topic": row["topic"], "count": row["count"]})

        return {
            "topics": topics,
            "total_topics": len(topics),
            "message": f"{len(topics)} ерекше тақырып табылды",
        }


@app.get("/topics/{topic}")
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

        results = []
        for row in rows:
            results.append(
                {
                    "id": row["id"],
                    "text": row["text"],
                    "topics": json.loads(row["topics"]),
                    "created_at": row["created_at"],
                }
            )

        return {
            "topic": topic,
            "results": results,
            "count": len(results),
            "message": f"'{topic}' тақырыбына {len(results)} мақал-мәтел табылды.",
        }
