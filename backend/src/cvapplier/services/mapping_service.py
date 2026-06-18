"""Mapping orchestrator: learned -> heuristics -> custom_answers -> LLM."""
import json
from collections.abc import Awaitable, Callable
from typing import Any

from cvapplier.core.config import get_settings
from cvapplier.core.logging import get_logger
from cvapplier.core.rate_limit import TokenBucketRateLimiter
from cvapplier.models.user import User
from cvapplier.repositories.cv_repository import CVRepository
from cvapplier.repositories.learned_mapping_repository import LearnedMappingRepository
from cvapplier.repositories.profile_repository import ProfileRepository
from cvapplier.services.heuristic_engine import (
    _FILE_VALUE_SENTINEL,
    ExtractedField,
    HeuristicEngine,
)
from cvapplier.services.llm_gateway import LLMGateway
from cvapplier.services.mapping_prompts import (
    build_resolve_prompt,
    sanitize_for_llm,
    SYSTEM_PROMPT,
)
from cvapplier.services.settings_service import SettingsService
from cvapplier.schemas.ws_messages import ProgressMsg, SessionCounts

log = get_logger(__name__)


class MappingService:
    def __init__(
        self,
        profile_repo: ProfileRepository | None = None,
        mapping_repo: LearnedMappingRepository | None = None,
        heuristics: HeuristicEngine | None = None,
        cv_repo: CVRepository | None = None,
    ) -> None:
        self.profile_repo = profile_repo or ProfileRepository()
        self.mapping_repo = mapping_repo or LearnedMappingRepository()
        self.heuristics = heuristics or HeuristicEngine()
        self.cv_repo = cv_repo or CVRepository()
        self._rate_limiters: dict[str, TokenBucketRateLimiter] = {}

    def _rate_limiter_for(self, user: User) -> TokenBucketRateLimiter:
        key = str(user.id)
        rl = self._rate_limiters.get(key)
        if rl is None:
            daily = int(user.settings.get("llm_daily_limit", 100))
            rl = TokenBucketRateLimiter(rate_per_min=60, burst=10, daily_limit=daily)
            self._rate_limiters[key] = rl
        return rl

    async def resolve_batch(
        self,
        user: User,
        fields: list[ExtractedField],
        *,
        language: str,
        ws_send: Callable[[ProgressMsg], Awaitable[None]],
    ) -> tuple[dict[str, Any], SessionCounts]:
        profile = await self.profile_repo.get_by_user(str(user.id))
        if profile is None:
            counts = SessionCounts(failed=len(fields))
            for f in fields:
                await ws_send(ProgressMsg(field_id=f.field_id, status="error", value=None))
            return {}, counts

        resolved: dict[str, Any] = {}
        counts = SessionCounts()

        # Stage 1: learned mappings
        sigs = [f.label or f.name or f.field_id for f in fields]
        learned = await self.mapping_repo.lookup(sigs, language=language)
        for f in fields:
            sig = f.label or f.name or f.field_id
            if sig in learned and learned[sig].confidence >= 0.85:
                value = self._resolve_profile_path(profile, learned[sig].target_path)
                if value is not None:
                    resolved[f.field_id] = value
                    counts.resolved_backend += 1
                    await ws_send(ProgressMsg(
                        field_id=f.field_id, status="learned", value=value,
                        confidence=learned[sig].confidence,
                    ))

        # Stage 2: server-side heuristics
        remaining = [f for f in fields if f.field_id not in resolved]
        heur_out = self.heuristics.resolve(remaining, profile)
        for f in remaining:
            if f.field_id in heur_out:
                val = heur_out[f.field_id]
                if val == _FILE_VALUE_SENTINEL:
                    continue  # handled in stage 2b below
                resolved[f.field_id] = val
                counts.resolved_backend += 1
                await ws_send(ProgressMsg(
                    field_id=f.field_id, status="local", value=val, confidence=0.9,
                ))

        # Stage 2b: resolve CV file fields with primary CV download URL
        cv_fields = [f for f in fields if f.field_id not in resolved and heur_out.get(f.field_id) == _FILE_VALUE_SENTINEL]
        if cv_fields:
            cvs = await self.cv_repo.list_for_user(str(user.id))
            primary = next((c for c in cvs if c.is_primary), cvs[0] if cvs else None)
            if primary:
                config = get_settings()
                api_base = getattr(config, "public_url", None) or "http://localhost:8000"
                for f in cv_fields:
                    resolved[f.field_id] = {
                        "__type": "cv_file",
                        "url": f"{api_base}/api/v1/cvs/{primary.id}/file",
                        "filename": primary.filename,
                        "mime_type": primary.mime_type,
                    }
                    counts.resolved_backend += 1
                    await ws_send(ProgressMsg(
                        field_id=f.field_id, status="learned",
                        value=primary.filename, confidence=0.95,
                    ))
            else:
                for f in cv_fields:
                    counts.failed += 1
                    await ws_send(ProgressMsg(
                        field_id=f.field_id, status="error",
                        value=None,
                    ))

        # Stage 3: custom answers cache
        still = [f for f in fields if f.field_id not in resolved]
        for f in still:
            answer = self._custom_answer_lookup(profile, f)
            if answer is not None:
                resolved[f.field_id] = answer
                counts.resolved_backend += 1
                await ws_send(ProgressMsg(
                    field_id=f.field_id, status="local", value=answer, confidence=0.8,
                ))

        # Stage 4: LLM
        still = [f for f in fields if f.field_id not in resolved]
        if still and user.settings.get("llm_enabled", True):
            rl = self._rate_limiter_for(user)
            if await rl.allow(str(user.id), n=len(still)):
                try:
                    llm_result = await self._llm_resolve(user, profile, still, language)
                    for f in still:
                        if f.field_id in llm_result and llm_result[f.field_id] is not None:
                            resolved[f.field_id] = llm_result[f.field_id]
                            counts.resolved_llm += 1
                            await ws_send(ProgressMsg(
                                field_id=f.field_id, status="llm",
                                value=llm_result[f.field_id], confidence=0.65,
                            ))
                        else:
                            counts.failed += 1
                            await ws_send(ProgressMsg(
                                field_id=f.field_id, status="skipped", value=None,
                            ))
                except Exception as e:
                    log.warning("llm_resolve_failed", user_id=str(user.id), error=str(e))
                    for f in still:
                        counts.failed += 1
                        await ws_send(ProgressMsg(
                            field_id=f.field_id, status="error", value=None,
                        ))
            else:
                for f in still:
                    counts.failed += 1
                    await ws_send(ProgressMsg(
                        field_id=f.field_id, status="skipped", value=None,
                    ))
        else:
            for f in still:
                counts.failed += 1
                await ws_send(ProgressMsg(
                    field_id=f.field_id, status="skipped", value=None,
                ))

        return resolved, counts

    def _resolve_profile_path(self, profile: Any, path: str) -> Any:
        import re
        cur: Any = profile
        for part in re.findall(r"[^.\[\]]+|\[\d+\]", path):
            if part.startswith("["):
                idx = int(part[1:-1])
                if isinstance(cur, list) and idx < len(cur):
                    cur = cur[idx]
                else:
                    return None
            else:
                cur = getattr(cur, part, None)
                if cur is None:
                    return None
        return cur

    def _custom_answer_lookup(self, profile: Any, f: ExtractedField) -> str | None:
        for c in (f.label, f.name, f.placeholder, f.context):
            if c and c in profile.custom_answers:
                return profile.custom_answers[c]
        return None

    async def _llm_resolve(
        self, user: User, profile: Any, fields: list[ExtractedField], language: str,
    ) -> dict[str, Any]:
        api_key = SettingsService().decrypt_api_key(user)
        gw = LLMGateway(
            provider=user.settings.get("llm_provider", "deepseek"),
            model=user.settings.get("llm_model", "deepseek-chat"),
            api_key=api_key,
            api_base=user.settings.get("ollama_base_url") or user.settings.get("custom_endpoint"),
        )
        sanitized = [
            {
                "field_id": f.field_id,
                "label": sanitize_for_llm(f.label or ""),
                "type": f.type,
                "name": sanitize_for_llm(f.name or ""),
                "placeholder": sanitize_for_llm(f.placeholder or ""),
                "options": f.options,
                "context": sanitize_for_llm(f.context or ""),
            }
            for f in fields
        ]
        user_msg = build_resolve_prompt(
            profile_json=json.dumps(profile.model_dump(mode="json"), default=str),
            fields_json=json.dumps(sanitized),
        )
        result = await gw.complete_json(system=SYSTEM_PROMPT, user_msg=user_msg, timeout=30)
        return result if isinstance(result, dict) else {}
