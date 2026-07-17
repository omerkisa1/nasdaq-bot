from fastapi import APIRouter

from db import repo

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
async def get_settings():
    return await repo.get_settings()


@router.patch("")
async def patch_settings(patch: dict):
    await repo.update_settings(patch)
    return await repo.get_settings()
