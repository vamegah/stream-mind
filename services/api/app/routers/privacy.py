from fastapi import APIRouter
from privacy import get_remaining_budget

router = APIRouter(prefix="/api/v1/privacy", tags=["privacy"])


@router.get("/budget/{user_token}")
async def get_privacy_budget(user_token: str):
    remaining = await get_remaining_budget(user_token)
    return {
        "user_token": user_token,
        "remaining_budget": remaining,
        "per_query_cost": 0.1,
        "daily_budget": 1.0,
    }
