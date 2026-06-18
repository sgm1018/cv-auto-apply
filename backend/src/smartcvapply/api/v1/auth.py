"""Auth endpoints."""
from fastapi import APIRouter, Depends, Response

from smartcvapply.core.deps import get_current_user
from smartcvapply.core.exceptions import AuthError, RateLimited
from smartcvapply.core.rate_limit import TokenBucketRateLimiter
from smartcvapply.models.user import User
from smartcvapply.schemas.auth_login import LoginRequest, LoginResponse
from smartcvapply.schemas.auth_me import MeResponse
from smartcvapply.schemas.auth_refresh import RefreshRequest, RefreshResponse
from smartcvapply.schemas.auth_register import RegisterRequest, RegisterResponse
from smartcvapply.services.auth_service import AuthService
from smartcvapply.services.onboarding_service import OnboardingService

router = APIRouter(prefix="/auth", tags=["auth"])

_login_limiter = TokenBucketRateLimiter(rate_per_min=10, burst=5)
_register_limiter = TokenBucketRateLimiter(rate_per_min=5, burst=3)
_refresh_limiter = TokenBucketRateLimiter(rate_per_min=10, burst=5)


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
    if not await _register_limiter.allow(req.email):
        raise RateLimited("Too many registration attempts")
    if not req.consent_terms:
        raise AuthError("Terms must be accepted")
    res = await AuthService().register(req.email, req.password, language=req.language)
    onboarding = await OnboardingService().get_status(str(res.user.id))
    return RegisterResponse(
        access_token=res.access_token,
        refresh_token=res.refresh_token,
        user_id=str(res.user.id),
        config_complete=onboarding["config_complete"],
        steps_config=onboarding["steps_config"],
    )


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, response: Response) -> LoginResponse:
    if not await _login_limiter.allow(req.email):
        raise RateLimited("Too many login attempts")
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
    if not await _refresh_limiter.allow(body.refresh_token[:32]):
        raise RateLimited("Too many refresh attempts")
    res = await AuthService().refresh(body.refresh_token)
    _set_refresh_cookie(response, res.refresh_token)
    return RefreshResponse(access_token=res.access_token, refresh_token=res.refresh_token)


@router.post("/logout")
async def logout(user: User = Depends(get_current_user)) -> dict:
    await AuthService().logout(str(user.id))
    return {"ok": True}


@router.get("/me", response_model=MeResponse)
async def me(user: User = Depends(get_current_user)) -> MeResponse:
    onboarding = await OnboardingService().get_status(str(user.id))
    return MeResponse(
        user_id=str(user.id),
        email=user.email,
        language=user.settings.get("language", "en"),
        llm_provider=user.settings.get("llm_provider", "deepseek"),
        llm_model=user.settings.get("llm_model", "deepseek-chat"),
        llm_enabled=user.settings.get("llm_enabled", True),
        config_complete=onboarding["config_complete"],
        steps_config=onboarding["steps_config"],
    )


@router.get("/onboarding", response_model=dict)
async def get_onboarding(user: User = Depends(get_current_user)) -> dict:
    return await OnboardingService().get_status(str(user.id))
