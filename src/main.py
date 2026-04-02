from __future__ import annotations

from fastapi import FastAPI

from .api.auth import router as auth_router
from .core.config import settings
from .core.exceptions import register_exception_handlers
from .core.logging import configure_logging
from .core.middleware import RequestIDMiddleware

configure_logging()

app = FastAPI(title=settings.app_name, debug=settings.debug, version=settings.version)

app.add_middleware(RequestIDMiddleware)
register_exception_handlers(app)
app.include_router(auth_router)
