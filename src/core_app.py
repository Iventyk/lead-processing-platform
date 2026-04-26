from fastapi import FastAPI

from src.exceptions.handlers import register_exception_handlers
from src.routers.analytics import router as analytics_router

app = FastAPI(title="Core Service", version="1.0.0")
app.include_router(analytics_router)
register_exception_handlers(app)
