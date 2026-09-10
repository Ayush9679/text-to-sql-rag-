"""FastAPI Application Entry Point for the Business Text-to-SQL Analytics Platform."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analytics, auth, conversations, datasets, dataquery, metrics
from app.config import get_settings
from app.database.session import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize metadata tables if needed
    try:
        init_db()
    except Exception as exc:
        print(f"Warning: Database init skipped during startup ({exc})")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Multi-Stage Business Data Intelligence, Profiling, Semantic RAG & Text-to-SQL Platform",
    lifespan=lifespan,
)

# CORS Configuration
allowed_origins = [
    settings.FRONTEND_URL.rstrip("/"),
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(auth.router)
app.include_router(datasets.router)
app.include_router(analytics.router)
app.include_router(conversations.router)
app.include_router(metrics.router)
app.include_router(dataquery.router)


@app.get("/", tags=["Health"])
@app.get("/health", tags=["Health"])
def health_check() -> dict:
    return {
        "status": "ok",
        "service": "text-to-sql-api",
        "version": "1.0.0",
        "llm_model": settings.GROQ_MODEL,
    }


def run():
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )


if __name__ == "__main__":
    run()
