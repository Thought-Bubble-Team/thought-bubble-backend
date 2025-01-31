from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except HTTPException as http_exception:
            logger.error(f"HTTP Exception: {http_exception.detail}")
            return JSONResponse(
                status_code=http_exception.status_code,
                content={"error": http_exception.detail},
            )
        except Exception as e:
            logger.exception("Unhandled exception occurred")
            return JSONResponse(
                status_code=500,
                content={"error": "An unexpected error occurred. Please try again later."},
            )
