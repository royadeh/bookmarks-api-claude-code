from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, closing

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import get_db_path
from app.db import connect, init_schema
from app.routes import bookmarks


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    with closing(connect(get_db_path())) as conn:
        init_schema(conn)
    yield


async def validation_error_handler(_: Request, error: Exception) -> JSONResponse:
    # Report field and reason only; never echo submitted values back.
    assert isinstance(error, RequestValidationError)
    detail = [{"loc": list(e["loc"]), "msg": e["msg"]} for e in error.errors()]
    return JSONResponse({"detail": detail}, status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)


def create_app() -> FastAPI:
    application = FastAPI(title="Bookmarks API",lifespan=lifespan)
    application.add_exception_handler(RequestValidationError, validation_error_handler)
    application.include_router(bookmarks.router)

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
