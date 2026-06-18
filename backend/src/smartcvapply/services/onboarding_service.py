"""Onboarding use cases: step tracking and completion checks."""
from smartcvapply.models.user import User, StepConfig
from smartcvapply.repositories.user_repository import UserRepository
from smartcvapply.services.settings_service import SettingsService


ONBOARDING_STEPS = ["api_key", "cv", "profile"]


class OnboardingService:
    def __init__(self, repo: UserRepository | None = None) -> None:
        self.repo = repo or UserRepository()

    async def get_status(self, user_id: str) -> dict:
        user = await self.repo.get_by_id(user_id)
        if user is None:
            return {"config_complete": False, "steps_config": _default_steps()}
        return {
            "config_complete": user.config_complete,
            "steps_config": user.steps_config,
        }

    async def auto_check_all(self, user_id: str) -> None:
        user = await self.repo.get_by_id(user_id)
        if user is None:
            return
        changed = False
        steps = {s["name"]: s for s in user.steps_config}

        api_key_ok = _step_api_key_done(user)
        if api_key_ok and not steps.get("api_key", {}).get("status"):
            _set_step(steps, "api_key", True)
            changed = True

        cv_ok = await _step_cv_done(user)
        if cv_ok and not steps.get("cv", {}).get("status"):
            _set_step(steps, "cv", True)
            changed = True

        profile_ok = await _step_profile_done(user)
        if profile_ok and not steps.get("profile", {}).get("status"):
            _set_step(steps, "profile", True)
            changed = True

        if not changed:
            return

        all_done = all(s["status"] for s in steps.values())
        user.steps_config = list(steps.values())
        user.config_complete = all_done
        await user.save()

    async def complete_step(self, user_id: str, step: str) -> None:
        if step not in ONBOARDING_STEPS:
            return
        user = await self.repo.get_by_id(user_id)
        if user is None:
            return
        steps = {s["name"]: s for s in user.steps_config}
        _set_step(steps, step, True)
        all_done = all(s["status"] for s in steps.values())
        user.steps_config = list(steps.values())
        user.config_complete = all_done
        await user.save()


# ── helpers ──────────────────────────────────────────────────────

def _default_steps() -> list[dict]:
    return [{"name": n, "status": False} for n in ONBOARDING_STEPS]


def _set_step(steps: dict, name: str, status: bool) -> None:
    if name in steps:
        steps[name]["status"] = status


def _step_api_key_done(user: User) -> bool:
    return bool(user.settings.get("llm_api_key_enc"))


async def _step_cv_done(user: User) -> bool:
    from smartcvapply.models.cv import CV
    from beanie import PydanticObjectId

    oid = PydanticObjectId(user.id)
    cv = await CV.find_one(
        CV.user_id == oid,
        CV.parse_status == "done",
    )
    return cv is not None


async def _step_profile_done(user: User) -> bool:
    from smartcvapply.models.profile import Profile
    from beanie import PydanticObjectId

    oid = PydanticObjectId(user.id)
    profile = await Profile.find_one(Profile.user_id == oid)
    if profile is None:
        return False
    return bool(profile.first_name and profile.email)
