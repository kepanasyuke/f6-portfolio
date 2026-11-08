"""Точка входа сервиса Hunt Rules."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app import api, config


def create_app() -> FastAPI:
    return mount_ui(mount_api(FastAPI(title=config.SERVICE_NAME, version=config.VERSION)))


def mount_api(application: FastAPI) -> FastAPI:
    application.include_router(api.router)
    return handlers(application)


def handlers(application: FastAPI) -> FastAPI:
    application.add_exception_handler(ValueError, on_invalid_rule)
    return application


async def on_invalid_rule(_request: Request, error: ValueError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"ok": False, "error": str(error), "detail": str(error)})


def mount_ui(application: FastAPI) -> FastAPI:
    return mount_root(mount_shared(application))


def mount_shared(application: FastAPI) -> FastAPI:
    application.mount("/shared", StaticFiles(directory=config.SHARED_DIR), name="shared")
    return application


def mount_root(application: FastAPI) -> FastAPI:
    application.mount("/", StaticFiles(directory=config.FRONTEND_DIR, html=True), name="ui")
    return application


app = create_app()
