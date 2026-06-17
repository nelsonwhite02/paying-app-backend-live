from fastapi import APIRouter, Depends
from db import db
from dependencies.auth import get_current_user

router = APIRouter(
    prefix="/referrals",
    tags=["Referrals"]
)

@router.get("/history")
async def referral_history(
    user=Depends(get_current_user)
):

    user_id = user["user_id"]

    referrals = []

    cursor = db.referral_rewards.find(
        {
            "referrer_id": user_id
        }
    )

    async for ref in cursor:

        referrals.append({
            "name":
                ref.get("referred_name", ""),
            "email":
                ref.get("referred_email", ""),
            "reward":
                ref.get("reward_amount", 0),
            "status":
                ref.get("status", "paid"),
            "date":
                str(ref.get("created_at")),
        })

    total = sum(
        r["reward"]
        for r in referrals
    )

    return {
        "total_earnings": total,
        "referrals": referrals,
    }