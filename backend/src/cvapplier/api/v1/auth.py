"""Auth endpoints."""
from fastapi import APIRouter, Depends, Response

from cvapplier.core.deps import get_current_user
from cvapplier.core.exceptions import AuthError
from cvapplier.models.user import User
from cvapplier.schemas.auth_login import LoginRequest, LoginResponse
from cvapplier.schemas.auth_me import MeResponse
from cvapplier.schemas.auth_refresh import RefreshRequest, RefreshResponse
from cvapplier.schemas.auth_register import RegisterRequest, RegisterResponse
from cvapplier.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=30 * 86400,
        path="/api/v1/auth",
    )


@router.post("/register", response_model=RegisterResponse)
async def register(req: RegisterRequest) -> RegisterResponse:
    if not req.consent_terms:
        raise AuthError("Terms must be accepted")
    res = await AuthService().register(req.email, req.password, language=req.language)
    return RegisterResponse(
        access_token=res.access_token,
        refresh_token=res.refresh_token,
        user_id=str(res.user.id),
    )


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, response: Response) -> LoginResponse:
    res = await AuthService().login(req.email, req.password)
    _set_refresh_cookie(response, res.refresh_token)
    return LoginResponse(
        access_token=res.access_token,
        refresh_token=res.refresh_token,
        user_id=str(res.user.id),
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(body: RefreshRequest, response: Response) -> RefreshResponse:
    if not body.refresh_token:
        raise AuthError("refresh_token required")
    res = await AuthService().refresh(body.refresh_token)
    _set_refresh_cookie(response, res.refresh_token)
    return RefreshResponse(access_token=res.access_token, refresh_token=res.refresh_token)


@router.post("/logout")
async def logout(user: User = Depends(get_current_user)) -> dict:
    await AuthService().logout(str(user.id))
    return {"ok": True}


@router.get("/me", response_model=MeResponse)
async def me(user: User = Depends(get_current_user)) -> MeResponse:
    return MeResponse(
        user_id=str(user.id),
        email=user.email,
        language=user.settings.get("language", "en"),
        llm_provider=user.settings.get("llm_provider", "deepseek"),
        llm_model=user.settings.get("llm_model", "deepseek-chat"),
        llm_enabled=user.settings.get("llm_enabled", True),
    )
