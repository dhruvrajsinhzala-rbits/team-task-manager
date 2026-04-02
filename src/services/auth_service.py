from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import (
    REFRESH_TOKEN_TYPE,
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    utc_now,
    verify_password,
)
from ..models.refresh_token import RefreshToken
from ..models.user import User
from ..schemas.auth import LoginRequest, RegisterRequest


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: RegisterRequest) -> User:
        result = await self.db.execute(select(User).where(User.email == str(data.email)))
        existing = result.scalar_one_or_none()
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        user = User(
            email=str(data.email),
            hashed_password=hash_password(data.password),
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def login(self, data: LoginRequest) -> dict[str, str]:
        result = await self.db.execute(select(User).where(User.email == str(data.email)))
        user = result.scalar_one_or_none()
        if user is None or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        access_token = create_access_token(user.id)
        refresh_token, refresh_expires_at = create_refresh_token(user.id)

        token_record = RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=refresh_expires_at,
        )
        self.db.add(token_record)
        await self.db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def refresh(self, refresh_token: str) -> dict[str, str]:
        try:
            token_payload = decode_token(refresh_token, expected_type=REFRESH_TOKEN_TYPE)
        except TokenError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
            ) from exc

        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token == refresh_token)
        )
        token_record = result.scalar_one_or_none()
        if token_record is None or token_record.is_revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token revoked",
            )

        if token_record.expires_at <= utc_now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired",
            )

        if token_record.user_id != token_payload.sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        token_record.is_revoked = True

        access_token = create_access_token(token_payload.sub)
        new_refresh_token, new_refresh_expires_at = create_refresh_token(token_payload.sub)
        self.db.add(
            RefreshToken(
                user_id=token_payload.sub,
                token=new_refresh_token,
                expires_at=new_refresh_expires_at,
            )
        )
        await self.db.commit()

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    async def logout(self, refresh_token: str) -> None:
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token == refresh_token)
        )
        token_record = result.scalar_one_or_none()
        if token_record is None or token_record.is_revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token invalid",
            )

        token_record.is_revoked = True
        await self.db.commit()

