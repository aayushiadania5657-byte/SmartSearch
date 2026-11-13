from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.health import router as health_router
from app.api.search import router as search_router
from app.api.documents import router as documents_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    description="AI-powered search and document discovery engine",
    version=settings.app_version,
    debug=settings.debug,
)

# Allow the local React frontend to communicate with the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(search_router)
app.include_router(documents_router)


@app.get("/")
def root():
    return {
        "message": "SmartSearch API is running",
        "version": settings.app_version,
    }