from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except HTTPException as http_exception:
            # Log HTTP error details
            logger.warning(
                f"HTTPException [{http_exception.status_code}]: {http_exception.detail} - "
                f"Path: {request.url.path}"
            )
            return JSONResponse(
                status_code=http_exception.status_code,
                content={"error": http_exception.detail, "path": request.url.path},
            )
        except Exception as e:
            # Log unexpected server errors with traceback
            logger.exception(
                f"Unhandled exception: {e} - "
                f"Path: {request.url.path} - Headers: {dict(request.headers)}"
            )
            return JSONResponse(
                status_code=500,
                content={"error": "Internal Server Error", "path": request.url.path},
            )