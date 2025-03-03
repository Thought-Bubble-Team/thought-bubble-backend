from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middlewares.exception_handler import ExceptionHandlerMiddleware
from app.middlewares.logging import setup_logging
from app.routes import journal_routes, sentiment_routes, mood_calender_routes

# Setup logging
setup_logging()

# Initialize FastAPI app
app = FastAPI(
    title="Journaling and Sentiment Analysis API",
    description="An API for managing journal entries and analyzing their sentiment.",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Add exception handler middleware
app.add_middleware(ExceptionHandlerMiddleware)

# Include routers
app.include_router(journal_routes.router, prefix="/api", tags=["Journal"])
app.include_router(sentiment_routes.router, prefix="/api", tags=["Sentiment Analysis"])
app.include_router(mood_calender_routes.router, prefix="/api", tags=["Mood Calendar"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}