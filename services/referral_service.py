from datetime import datetime

from db import db
from services.wallet import credit_wallet
from bson import ObjectId

REFERRAL_BONUS = 100

async def process_referral_reward(user_id: str):

    user = await db.users.find_one({
        "_id": ObjectId(user_id)
    })

    if not user:
        return

    if user.get("referral_rewarded"):
        return

    referral_code = user.get("referred_by")

    if not referral_code:
        return

    referrer = await db.users.find_one({
        "referral_code": referral_code
    })

    if not referrer:
        return

    referrer_id = str(referrer["_id"])

    reference = f"REF-{user_id}"

    await credit_wallet(
        user_id=referrer_id,
        amount=REFERRAL_BONUS,
        reference=reference
    )

    await db.users.update_one(
        {
            "_id": referrer["_id"]
        },
        {
            "$inc": {
                "referral_count": 1,
                "referral_earnings": REFERRAL_BONUS
            }
        }
    )

    await db.users.update_one(
        {
            "_id": user["_id"]
        },
        {
            "$set": {
                "referral_rewarded": True,
                "referral_rewarded_at": datetime.utcnow()
            }
        }
    )

    print(
        f"🎉 Referral reward paid to {referrer_id}"
    )