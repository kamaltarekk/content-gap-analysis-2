from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.db.session import create_all


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Local/dev convenience: ensure tables exist. Controlled environments run Alembic.
    create_all()
    yield


app = FastAPI(title="Content Diagnosis API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
