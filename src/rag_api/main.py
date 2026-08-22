"""FastAPI application factory."""

from fastapi import FastAPI

from rag_api.api.errors import register_error_handlers
from rag_api.api.lifespan import lifespan
from rag_api.api.logging import configure_logging
from rag_api.api.middleware import RequestContextMiddleware
from rag_api.api.routes import answers, health
from rag_api.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    configure_logging(settings.log_level)
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.add_middleware(RequestContextMiddleware)
    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(answers.router)
    return app


app = create_app()
