"""Exception hierarchy and global error handler."""
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from cvapplier.core.logging import get_logger

log = get_logger(__name__)


class AppError(Exception):
    code: str = "internal_error"
    http_status: int = 500
    message: str = "Internal server error"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.message)
        if message:
            self.message = message


class AuthError(AppError):
    code = "unauthorized"
    http_status = 401
    message = "Unauthorized"


class ForbiddenError(AppError):
    code = "forbidden"
    http_status = 403
    message = "Forbidden"


class NotFoundError(AppError):
    code = "not_found"
    http_status = 404
    message = "Not found"


class ValidationFailed(AppError):
    code = "validation_failed"
    http_status = 422
    message = "Validation failed"


class RateLimited(AppError):
    code = "rate_limited"
    http_status = 429
    message = "Too many requests"


class LLMError(AppError):
    code = "llm_error"
    http_status = 502
    message = "LLM provider error"


class LLMInvalidKeyError(LLMError):
    code = "llm_invalid_key"
    message = "LLM API key is invalid"


class LLMTimeoutError(LLMError):
    code = "llm_timeout"
    message = "LLM provider timed out"


class LLMNotConfigured(LLMError):
    code = "llm_not_configured"
    http_status = 503
    message = "LLM provider is not configured"


class UpstreamError(AppError):
    code = "upstream_error"
    http_status = 502
    message = "Upstream service error"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _handler(_request: Request, exc: AppError) -> JSONResponse:
        request_id = str(uuid.uuid4())
        log.warning("app_error", code=exc.code, status=exc.http_status,
                    request_id=request_id, message=exc.message)
        return JSONResponse(
            status_code=exc.http_status,
            content={"code": exc.code, "message": exc.message, "request_id": request_id},
        )
