from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import health, llm
from app.config import get_settings
from app.core.database import build_engine, init_database


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = build_engine(settings.database_url)
        init_database(engine)
        app.state.engine = engine
        yield
        engine.dispose()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.include_router(health.router)
    app.include_router(llm.router)
    return app


app = create_app()
