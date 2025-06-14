from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router as api_router
from app.database import init_db


# Initialize db on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Maqal-matel API", lifespan=lifespan)

app.include_router(api_router)
