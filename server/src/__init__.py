from fastapi import FastAPI, status
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from src.api import api_router
from src.core import init_db, create_fts_table, engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)
from src.data.ml import _load_models_if_needed


@asynccontextmanager
async def life_span(app: FastAPI):
    print("Application is starting...")
    await init_db()

    # Create FTS table once DB is ready
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        await create_fts_table(session)

    # Cache ML models at startup
    await _load_models_if_needed()

    yield
    print("Application is shutting down...")


app = FastAPI(title="FilmFlare", description="FilmFlare API", lifespan=life_span)


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Development origin
        # "https://your-production-domain.com"  # Production origin
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)


@app.get("/", status_code=status.HTTP_200_OK)
async def health() -> dict[str, str]:
    return {"status": "ok", "message": "Hello from server!"}
