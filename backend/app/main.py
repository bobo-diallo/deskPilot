from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import agent, costs, extractions, health, llm, reviews, search, test_page
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
    app.include_router(extractions.router)
    app.include_router(reviews.router)
    app.include_router(search.router)
    app.include_router(agent.router)
    app.include_router(costs.router)
    app.include_router(test_page.router)
    return app


app = create_app()
