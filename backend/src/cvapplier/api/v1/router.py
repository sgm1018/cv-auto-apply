"""Aggregate v1 routers."""
from fastapi import APIRouter

from cvapplier.api.v1 import auth, cvs, feedback, mappings, profile, sessions, settings, system, users, ws

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(profile.router)
api_router.include_router(settings.router)
api_router.include_router(cvs.router)
api_router.include_router(mappings.router)
api_router.include_router(feedback.router)
api_router.include_router(sessions.router)
api_router.include_router(users.router)
api_router.include_router(system.router)
api_router.include_router(ws.router)
