import logging
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse

REQUEST_ID_HEADER = "X-Request-ID"

logger = logging.getLogger(__name__)


async def request_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    # Always generate the ID server-side; client-supplied values are not trusted.
    request.state.request_id = uuid.uuid4().hex
    response = await call_next(request)
    response.headers[REQUEST_ID_HEADER] = request.state.request_id
    return response


async def internal_error_handler(request: Request, error: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", uuid.uuid4().hex)
    logger.error("Unhandled error, request_id=%s", request_id, exc_info=error)
    return JSONResponse(
        {"detail": "Internal server error", "request_id": request_id},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        headers={REQUEST_ID_HEADER: request_id},
    )
