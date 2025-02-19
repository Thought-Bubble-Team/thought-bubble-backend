from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

# Initialize logger
logger = logging.getLogger(__name__)

class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            # Proceed with the request
            response = await call_next(request)
            return response
        except HTTPException as http_exception:
            # Log HTTP exceptions with details
            logger.error(
                f"HTTP Exception: {http_exception.detail} - "
                f"Status: {http_exception.status_code} - "
                f"Path: {request.url.path}"
            )
            return JSONResponse(
                status_code=http_exception.status_code,
                content={
                    "error": http_exception.detail,
                    "path": request.url.path,
                },
            )
        except Exception as e:
            # Log unhandled exceptions with additional details
            logger.exception(
                f"Unhandled exception occurred: {e} - "
                f"Path: {request.url.path} - "
                f"Headers: {dict(request.headers)}"
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "An unexpected error occurred. Please try again later.",
                    "path": request.url.path,
                },
            )