from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.apis.api import api_router
from core.config.settings import get_settings
from core.database.mongodb import mongo_manager
from core.database.indexes import ensure_indexes
from core.utils.app_logging import configure_debug_logging, get_logger


configure_debug_logging()
logger = get_logger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.project_name,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = jsonable_encoder(exc.errors())
        logger.error(
            "422 Validation error method=%s path=%s errors=%s",
            request.method,
            request.url.path,
            errors,
        )
        return JSONResponse(status_code=422, content={"detail": errors})

    @app.middleware("http")
    async def request_debug_logger(request, call_next):
        started_at = perf_counter()
        logger.info("HTTP request started method=%s path=%s", request.method, request.url.path)
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("HTTP request crashed method=%s path=%s", request.method, request.url.path)
            raise

        duration_ms = round((perf_counter() - started_at) * 1000, 2)
        logger.info(
            "HTTP request completed method=%s path=%s status=%s duration_ms=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

    @app.on_event("startup")
    async def startup_event() -> None:
        logger.info("Application startup initiated")
        await mongo_manager.connect(settings)
        await ensure_indexes()
        logger.info("Application startup completed")

    @app.on_event("shutdown")
    async def shutdown_event() -> None:
        logger.info("Application shutdown initiated")
        await mongo_manager.disconnect()
        logger.info("Application shutdown completed")

    app.include_router(api_router, prefix="/api")
    return app


app = create_app()
