from fastapi import FastAPI, HTTPException
from app.database import init_db, get_db
from typing import List
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
