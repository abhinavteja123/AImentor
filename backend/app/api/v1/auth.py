"""
Authentication API Endpoints
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.postgres import get_db
from ...schemas.user import (
    UserRegister, 
    UserLogin, 
    UserResponse, 
    TokenResponse,
    RefreshTokenRequest
)
from ...services.auth_service import AuthService
from ...utils.security import get_current_user

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.
    
    - **email**: Valid email address (must be unique)
    - **password**: Min 8 chars, 1 uppercase, 1 lowercase, 1 number
    - **full_name**: User's full name
    """
    auth_service = AuthService(db)
    result = await auth_service.register_user(
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name
    )
    return result


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password.
    
    Returns access token and refresh token.
    """
    auth_service = AuthService(db)
    result = await auth_service.login_user(
        email=form_data.username,
        password=form_data.password
    )
    return result


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    """
    auth_service = AuthService(db)
    result = await auth_service.refresh_access_token(request.refresh_token)
    return result


@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user and invalidate token.
    """
    auth_service = AuthService(db)
    await auth_service.logout_user(token)
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_user)
):
    """
    Get current authenticated user information.
    """
    return current_user
