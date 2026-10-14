from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, closing

from fastapi import FastAPI

from app.config import get_db_path
from app.db import connect, init_schema


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    with closing(connect(get_db_path())) as conn:
        init_schema(conn)
    yield


def create_app() -> FastAPI:
    application = FastAPI(title="Bookmarks API", lifespan=lifespan)

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
