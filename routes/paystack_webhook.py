import hashlib
import hmac
import os
from datetime import datetime
from fastapi import APIRouter, Request, Header, HTTPException
from services.referral_service import process_referral_reward

from services.wallet import credit_wallet
from db.db import transactions_collection

router = APIRouter()

PAYSTACK_SECRET = os.getenv("PAYSTACK_SECRET_KEY")


# ======================================================
# 🔐 VERIFY SIGNATURE
# ======================================================
def verify_signature(body: bytes, signature: str):
    computed = hmac.new(
        PAYSTACK_SECRET.encode(),
        body,
        hashlib.sha512,
    ).hexdigest()

    return hmac.compare_digest(computed, signature)


# ======================================================
# 🔔 PAYSTACK WEBHOOK
# ======================================================
@router.post("/paystack/webhook")
async def paystack_webhook(
    request: Request,
    x_paystack_signature: str = Header(None),
):
    body = await request.body()

    # ❌ Reject if signature invalid
    if not x_paystack_signature or not verify_signature(body, x_paystack_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    event = payload.get("event")
    data = payload.get("data", {})

    print("🔔 PAYSTACK WEBHOOK RECEIVED:", event)

    # ======================================================
    # ✅ PAYMENT SUCCESS
    # ======================================================
    if event == "charge.success":

        reference = data.get("reference")
        amount = (data.get("amount", 0)) / 100  # Kobo → Naira

        metadata = data.get("metadata", {})
        user_id = metadata.get("user_id")

        if not user_id:
            print("❌ Missing user_id in metadata")
            return {"status": "ignored"}

        # ==================================================
        # 🛑 PREVENT DUPLICATE CREDIT
        # ==================================================
        existing = transactions_collection.find_one({
            "reference": reference
        })

        if existing:
            print("⚠️ Duplicate webhook ignored:", reference)
            return {"status": "duplicate_ignored"}

        print("💰 Crediting wallet:", user_id, amount)

        # ==================================================
        # 💳 CREDIT WALLET
        # ==================================================
        await credit_wallet(
            user_id=user_id,
            amount=amount,
            reference=reference,
        )

        await process_referral_reward(user_id)

        # ==================================================
        # 🧾 SAVE TRANSACTION
        # ==================================================
        transactions_collection.insert_one({
            "user_id": user_id,
            "reference": reference,
            "amount": amount,
            "type": "credit",
            "title": "Wallet Funding (Paystack)",
            "status": "success",
            "created_at": datetime.utcnow()
        })

        print("✅ Transaction saved:", reference)

    return {"status": "ok"}