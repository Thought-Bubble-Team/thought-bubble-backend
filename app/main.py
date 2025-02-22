from fastapi import FastAPI

from app.middlewares.exception_handler import ExceptionHandlerMiddleware
from app.middlewares.logging import setup_logging
from app.routes import journal_routes, sentiment_routes

# Setup logging
setup_logging()

# Initialize FastAPI app
app = FastAPI(
    title="Journaling and Sentiment Analysis API",
    description="An API for managing journal entries and analyzing their sentiment.",
    version="1.0.0",
)

# Add exception handler middleware
app.add_middleware(ExceptionHandlerMiddleware)

# Include routers
app.include_router(journal_routes.router, prefix="/api", tags=["Journal"])
app.include_router(sentiment_routes.router, prefix="/api", tags=["Sentiment Analysis"])
