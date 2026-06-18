"""Settings endpoints."""
from fastapi import APIRouter, Depends

from smartcvapply.core.deps import get_current_user
from smartcvapply.models.user import User
from smartcvapply.schemas.settings_get import SettingsResponse
from smartcvapply.schemas.settings_update import LLMTestRequest, LLMTestResponse, SettingsUpdateRequest
from smartcvapply.services.llm_gateway import LLMGateway
from smartcvapply.services.onboarding_service import OnboardingService
from smartcvapply.services.settings_service import SettingsService

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
async def get_settings(user: User = Depends(get_current_user)) -> SettingsResponse:
    return SettingsResponse(**(await SettingsService().get(user)))


@router.patch("", response_model=SettingsResponse)
async def patch_settings(
    body: SettingsUpdateRequest,
    user: User = Depends(get_current_user),
) -> SettingsResponse:
    patch = body.model_dump(exclude_unset=True)
    result = SettingsResponse(**(await SettingsService().update(user, patch)))
    if "llm_api_key" in body.model_dump(exclude_unset=True):
        await OnboardingService().auto_check_all(str(user.id))
    return result


@router.post("/llm/test", response_model=LLMTestResponse)
async def llm_test(body: LLMTestRequest = LLMTestRequest(), user: User = Depends(get_current_user)) -> LLMTestResponse:
    saved_key = SettingsService().decrypt_api_key(user)
    api_key = body.api_key or saved_key
    provider = body.provider or user.settings.get("llm_provider", "deepseek")
    model = body.model or user.settings.get("llm_model", "deepseek-chat")
    api_base = user.settings.get("ollama_base_url") or user.settings.get("custom_endpoint")
    gw = LLMGateway(
        provider=provider,
        model=model,
        api_key=api_key,
        api_base=api_base,
    )
    try:
        await gw.ping()
        return LLMTestResponse(ok=True, model=gw.model_string, message="LLM reachable")
    except Exception as e:
        return LLMTestResponse(ok=False, model=gw.model_string, message=str(e))
