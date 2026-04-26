from fastapi import FastAPI

from src.exceptions.handlers import register_exception_handlers
from src.routers.landings import router as landings_router

app = FastAPI(title="Landings Service", version="1.0.0")
app.include_router(landings_router)
register_exception_handlers(app)
