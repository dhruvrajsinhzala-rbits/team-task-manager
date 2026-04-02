from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from .config import settings

ALGORITHM = "HS256"

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


@dataclass(frozen=True, slots=True)
class TokenPayload:
    sub: str
    token_type: str


class TokenError(Exception):
    pass


def _create_token(*, subject: str, token_type: str, expires_delta: timedelta) -> tuple[str, datetime]:
    now = utc_now()
    expires_at = now + expires_delta
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": expires_at,
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)
    return token, expires_at


def create_access_token(subject: str) -> str:
    token, _ = _create_token(
        subject=subject,
        token_type=ACCESS_TOKEN_TYPE,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return token


def create_refresh_token(subject: str) -> tuple[str, datetime]:
    return _create_token(
        subject=subject,
        token_type=REFRESH_TOKEN_TYPE,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str, *, expected_type: str | None = None) -> TokenPayload:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except ExpiredSignatureError as exc:
        raise TokenError("Token expired") from exc
    except InvalidTokenError as exc:
        raise TokenError("Invalid token") from exc

    subject = payload.get("sub")
    token_type = payload.get("type")

    if not isinstance(subject, str) or not subject:
        raise TokenError("Invalid token subject")
    if not isinstance(token_type, str) or not token_type:
        raise TokenError("Invalid token type")
    if expected_type is not None and token_type != expected_type:
        raise TokenError("Invalid token type")

    return TokenPayload(sub=subject, token_type=token_type)

