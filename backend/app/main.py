"""Punkt wejścia FastAPI.

Routery modułów są odkrywane automatycznie: każdy plik `app/modules/<nazwa>/router.py`
eksportujący `router: APIRouter` trafia pod `/api/<nazwa>`. Rejestr nie istnieje —
dodanie modułu to dodanie katalogu, bez edycji tego pliku.
"""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.contracts import AppMeta, Health
from app.core.errors import AppError, app_error_handler
from app.core.logging import configure_logging
from app.core.settings import settings
from app.modules.auth.deps import current_user

log = structlog.get_logger(__name__)

MODULES_PACKAGE = "app.modules"

#: Moduły dostępne bez logowania. `auth` musi być publiczny, żeby dało się
#: zalogować; `system` to `/health` i `/meta`, po które sięga pasek nagłówka
#: jeszcze przed zalogowaniem.
PUBLIC_MODULES = frozenset({"auth", "system"})


def discover_routers() -> list[tuple[str, APIRouter]]:
    """Zwraca (nazwa_modułu, router) dla każdego modułu z router.py."""
    found: list[tuple[str, APIRouter]] = []
    package = importlib.import_module(MODULES_PACKAGE)
    for info in pkgutil.iter_modules(package.__path__):
        if not info.ispkg:
            continue
        try:
            module = importlib.import_module(f"{MODULES_PACKAGE}.{info.name}.router")
        except ModuleNotFoundError as exc:
            if exc.name and exc.name.endswith(".router"):
                log.debug("module_without_router", module=info.name)
                continue
            raise
        router = getattr(module, "router", None)
        if isinstance(router, APIRouter):
            found.append((getattr(module, "PREFIX", info.name), router))
        else:
            log.warning("module_router_invalid", module=info.name)
    return sorted(found, key=lambda item: item[0])


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    log.info(
        "startup",
        version=settings.version,
        offline=settings.offline,
        modules=settings.module_modes(),
    )
    yield
    log.info("shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Redactions"],
    )
    app.add_exception_handler(AppError, app_error_handler)

    system = APIRouter(tags=["system"])

    @system.get("/health", response_model=Health)
    def health() -> Health:
        modes = settings.module_modes()
        return Health(
            status="ok",
            version=settings.version,
            modules={name: mode for name, mode in modes.items()},
        )

    @system.get("/meta", response_model=AppMeta)
    def meta() -> AppMeta:
        return AppMeta(
            name=settings.app_name,
            version=settings.version,
            offline=settings.offline,
            module_modes=settings.module_modes(),
        )

    app.include_router(system, prefix="/api")

    for name, router in discover_routers():
        # Bramka na całym module: bez tokenu nie odpowiada nawet odczyt.
        # `current_user` zwraca pierwszego użytkownika przy `AUTH_ENABLED=false`,
        # więc demo i testy działają bez logowania.
        gate = [] if name in PUBLIC_MODULES else [Depends(current_user)]
        app.include_router(router, prefix=f"/api/{name}", dependencies=gate)
        log.info("router_mounted", module=name, prefix=f"/api/{name}")

    return app


app = create_app()
