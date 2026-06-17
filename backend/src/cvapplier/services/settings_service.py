"""Settings use cases with encrypted LLM API key handling."""
from cvapplier.core.config import get_settings
from cvapplier.core.exceptions import ValidationFailed
from cvapplier.models.user import User
from cvapplier.repositories.user_repository import UserRepository
from cvapplier.services.encryption import decrypt_api_key, encrypt_api_key


VALID_MODELS = {
    "deepseek": ["deepseek-chat", "deepseek-reasoner", "deepseek-coder"],
    "openai": ["gpt-4o-mini", "gpt-4.1-mini"],
    "anthropic": ["claude-3-5-haiku-20241022"],
    "ollama": ["llama3.1:8b-instruct-q4_K_M", "qwen2.5:7b-instruct-q4_K_M"],
    "custom": None,
}


class SettingsService:
    def __init__(self, repo: UserRepository | None = None) -> None:
        self.repo = repo or UserRepository()

    async def get(self, user: User) -> dict:
        s = user.settings
        return {
            "language": s.get("language", "en"),
            "autofill_mode": s.get("autofill_mode", "review"),
            "llm_enabled": s.get("llm_enabled", True),
            "llm_provider": s.get("llm_provider", "deepseek"),
            "llm_model": s.get("llm_model", "deepseek-chat"),
            "llm_api_key_set": bool(s.get("llm_api_key_enc")),
            "ollama_base_url": s.get("ollama_base_url"),
            "custom_endpoint": s.get("custom_endpoint"),
            "llm_daily_limit": s.get("llm_daily_limit", 100),
            "notifications_enabled": s.get("notifications_enabled", True),
        }

    async def update(self, user: User, patch: dict) -> dict:
        s = get_settings()
        if "llm_api_key" in patch:
            if patch["llm_api_key"]:
                patch["llm_api_key_enc"] = encrypt_api_key(
                    patch.pop("llm_api_key"), fernet_key=s.fernet_key,
                )
            else:
                patch["llm_api_key_enc"] = None
                patch.pop("llm_api_key")

        if "llm_provider" in patch:
            allowed = VALID_MODELS[patch["llm_provider"]]
            if allowed is not None and patch.get("llm_model") not in allowed:
                raise ValidationFailed(
                    f"Model {patch.get('llm_model')} not allowed for provider {patch['llm_provider']}"
                )

        await self.repo.update_settings(str(user.id), patch)
        updated = await self.repo.get_by_id(str(user.id))
        assert updated is not None
        return await self.get(updated)

    def decrypt_api_key(self, user: User) -> str | None:
        s = get_settings()
        enc = user.settings.get("llm_api_key_enc")
        if not enc:
            return None
        try:
            return decrypt_api_key(enc, fernet_key=s.fernet_key)
        except Exception:
            return None
