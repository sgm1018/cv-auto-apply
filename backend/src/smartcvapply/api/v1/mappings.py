"""Learned mappings lookup endpoint."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from smartcvapply.core.deps import get_current_user
from smartcvapply.models.user import User
from smartcvapply.repositories.learned_mapping_repository import LearnedMappingRepository
from smartcvapply.schemas.mapping_lookup import LearnedLookupResponse, LearnedMappingDTO

router = APIRouter(prefix="/mappings", tags=["mappings"])


@router.get("/learned", response_model=LearnedLookupResponse)
async def lookup_learned(
    signatures: Annotated[list[str], Query()],
    language: Annotated[str, Query(pattern="^(en|es)$")] = "en",
    _user: User = Depends(get_current_user),
) -> LearnedLookupResponse:
    items = await LearnedMappingRepository().lookup(signatures, language=language)
    return LearnedLookupResponse(
        mappings={
            sig: LearnedMappingDTO(
                field_signature=m.field_signature,
                target_path=m.target_path,
                transform=m.transform,
                confidence=m.confidence,
                usage_count=m.usage_count,
            )
            for sig, m in items.items()
        }
    )
