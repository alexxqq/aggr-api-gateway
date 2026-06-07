"""FastAPI application entrypoint."""

import logging
import re
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.routing import APIRoute

from app.api.routes import router
from app.core.config import get_settings
from app.core.firebase import init_firebase

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Eagerly init Firebase at startup (logs a warning if credentials not set)
    init_firebase()
    yield


def _route_id(route: APIRoute) -> str:
    """
    Stable operation_id based on path only.

    FastAPI's default uses `list(route.methods)[0]` (set — unpredictable) so all
    methods on a multi-method route get the same random suffix.  Using path-only
    gives one deterministic ID per route; each (path, method) combination in the
    OpenAPI spec still gets its own entry in Swagger UI.
    """
    slug = re.sub(r"\W+", "_", route.path_format).strip("_")
    return slug or "root"


def create_app() -> FastAPI:
    settings = get_settings()
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

    app = FastAPI(
        title="API Gateway",
        description=(
            "Single public entry point for the blockchain payment aggregator.\n\n"
            "## Authentication\n\n"
            "All `/v1/*` endpoints require a Firebase ID token supplied as a "
            "Bearer token in the `Authorization` header.\n\n"
            "**Local dev bypass:** set `DEV_BYPASS_TOKEN` in `.env` and send that "
            "value as the Bearer token together with an `X-Dev-Firebase-Uid` header "
            "to skip live Firebase verification."
        ),
        version="0.1.0",
        lifespan=lifespan,
        generate_unique_id_function=_route_id,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    @app.exception_handler(BrokenPipeError)
    async def _broken_pipe(_req: Request, _exc: BrokenPipeError) -> Response:
        """Client disconnected mid-response — suppress the noisy traceback."""
        logger.debug("BrokenPipeError: client disconnected")
        return Response(status_code=499)

    @app.exception_handler(ConnectionResetError)
    async def _conn_reset(_req: Request, _exc: ConnectionResetError) -> Response:
        """Client reset the connection — suppress the noisy traceback."""
        logger.debug("ConnectionResetError: client disconnected")
        return Response(status_code=499)

    return app


app = create_app()


@app.get("/health")
async def health():
    return {"status": "ok"}
