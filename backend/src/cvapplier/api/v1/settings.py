"""Settings endpoints."""
from fastapi import APIRouter, Depends

from cvapplier.core.deps import get_current_user
from cvapplier.models.user import User
from cvapplier.schemas.settings_get import SettingsResponse
from cvapplier.schemas.settings_update import LLMTestResponse, SettingsUpdateRequest
from cvapplier.services.llm_gateway import LLMGateway
from cvapplier.services.settings_service import SettingsService

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
    return SettingsResponse(**(await SettingsService().update(user, patch)))


@router.post("/llm/test", response_model=LLMTestResponse)
async def llm_test(user: User = Depends(get_current_user)) -> LLMTestResponse:
    api_key = SettingsService().decrypt_api_key(user)
    gw = LLMGateway(
        provider=user.settings.get("llm_provider", "deepseek"),
        model=user.settings.get("llm_model", "deepseek-chat"),
        api_key=api_key,
        api_base=user.settings.get("ollama_base_url") or user.settings.get("custom_endpoint"),
    )
    try:
        await gw.ping()
        return LLMTestResponse(ok=True, model=gw.model_string, message="LLM reachable")
    except Exception as e:
        return LLMTestResponse(ok=False, model=gw.model_string, message=str(e))
