from fastapi import FastAPI
from app.middlewares.exception_handler import ExceptionHandlerMiddleware
from app.middlewares.logging import setup_logging
from app.routes.journal_routes import router as journal_router
from app.routes.sentiment_routes import router as sentiment_router

# Setup logging
setup_logging()

# Initialize FastAPI app
app = FastAPI()
app.add_middleware(ExceptionHandlerMiddleware)

# Include routers
app.include_router(journal_router, prefix="/api", tags=["Journal"])
app.include_router(sentiment_router, prefix="/api", tags=["Sentiment Analysis"])
