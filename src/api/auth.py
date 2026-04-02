from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import get_db
from ..schemas.auth import LoginRequest, LogoutRequest, RefreshRequest, RegisterRequest, UserPublic
from ..services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    user = await service.register(data)

    return {
        "status": True,
        "message": "User registered successfully",
        "data": UserPublic.model_validate(user).model_dump(),
        "error": None,
    }


@router.post("/login")
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    tokens = await service.login(data)

    return {
        "status": True,
        "message": "Login successful",
        "data": tokens,
        "error": None,
    }


@router.post("/refresh")
async def refresh(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    tokens = await service.refresh(data.refresh_token)

    return {
        "status": True,
        "message": "Token refreshed",
        "data": tokens,
        "error": None,
    }


@router.post("/logout")
async def logout(
    data: LogoutRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    await service.logout(data.refresh_token)

    return {
        "status": True,
        "message": "Logged out",
        "data": None,
        "error": None,
    }

