from fastapi import FastAPI

from app.api.routes import health, ingest, query
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.APP_NAME)

app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(query.router)
