from fastapi import APIRouter, Response, status

from auth.dependencies.auth import CurrentUserIdDep
from auth.dependencies.service import AuthServiceDep
from auth.schemas.token import (
    LogoutRequest,
    RefreshTokenRequest,
    TokenPairResponse,
)
from auth.schemas.user import UserLoginRequest, UserRegisterRequest, UserResponse
from shared.core.exceptions import (
    BadRequestException,
    NotFoundException,
    UnauthorizedException,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse
)
async def register_user(payload: UserRegisterRequest, auth_service: AuthServiceDep):
    try:
        user = await auth_service.register_user(payload.email, payload.password)
    except ValueError:
        raise BadRequestException(detail="An account with this email already exists.")
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenPairResponse)
async def login(payload: UserLoginRequest, auth_service: AuthServiceDep):
    try:
        user = await auth_service.authenticate_user(payload.email, payload.password)
        return await auth_service.issue_tokens(user.id)
    except ValueError as exc:
        raise UnauthorizedException(detail=str(exc)) from exc


@router.post("/refresh", response_model=TokenPairResponse)
async def refresh(payload: RefreshTokenRequest, auth_service: AuthServiceDep):
    try:
        return await auth_service.rotate_refresh_token(payload.refresh_token)
    except ValueError as exc:
        raise UnauthorizedException(detail=str(exc)) from exc


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: LogoutRequest, auth_service: AuthServiceDep):
    try:
        await auth_service.logout(payload.refresh_token)
    except ValueError as exc:
        raise UnauthorizedException(detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserResponse)
async def me(current_user_id: CurrentUserIdDep, auth_service: AuthServiceDep):
    user = await auth_service.get_user_profile(current_user_id)
    if not user:
        raise NotFoundException(detail="User not found")
    return UserResponse.model_validate(user)
