from __future__ import annotations

import time
import uuid

import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars

from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = structlog.get_logger()


class RequestIDMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())
        method = scope.get("method")
        path = scope.get("path")

        clear_contextvars()
        bind_contextvars(request_id=request_id)

        start_time = time.monotonic()
        status_code: int | None = None

        scope.setdefault("state", {})
        scope["state"]["request_id"] = request_id

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode("utf-8")))
                message["headers"] = headers

            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = (time.monotonic() - start_time) * 1000
            logger.info(
                "request",
                method=method,
                path=path,
                status_code=status_code or 500,
                duration_ms=round(duration_ms, 2),
            )
            clear_contextvars()
