from datetime import datetime
import uuid
import json
import hmac
import hashlib
import os
import requests

from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel
from pymongo import ReturnDocument

from db.db import transactions_collection, wallets_collection

router = APIRouter(prefix="/payments/paystack", tags=["Paystack"])

# ==========================================================
# CONFIG
# ==========================================================
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")

PAYSTACK_INIT_URL = "https://api.paystack.co/transaction/initialize"
PAYSTACK_VERIFY_URL = "https://api.paystack.co/transaction/verify/"

HEADERS = {
    "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
    "Content-Type": "application/json",
}

# ==========================================================
# SCHEMA
# ==========================================================
class PaystackInitRequest(BaseModel):
    amount: float
    email: str
    user_id: str   # ⚠️ Keep for now (later replace with JWT)

# ==========================================================
# INIT PAYMENT
# ==========================================================
@router.post("/init")
def init_payment(payload: PaystackInitRequest):

    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    reference = str(uuid.uuid4())

    print("🔥 INIT CALLED")
    print("🧾 REF:", reference)
    print("👤 USER:", payload.user_id)

    response = requests.post(
        PAYSTACK_INIT_URL,
        headers=HEADERS,
        json={
            "email": payload.email,
            "amount": int(payload.amount * 100),
            "reference": reference,
            "metadata": {
                "user_id": payload.user_id,
            },
        },
    )

    data = response.json()

    if not data.get("status"):
        raise HTTPException(status_code=400, detail="Paystack init failed")

    # ✅ SAVE TRANSACTION
    transactions_collection.insert_one({
        "reference": reference,
        "user_id": payload.user_id,
        "amount": payload.amount,
        "status": "pending",
        "type": "credit",
        "created_at": datetime.utcnow(),
    })

    return {
        "checkout_url": data["data"]["authorization_url"],
        "reference": reference,
    }

# ==========================================================
# VERIFY PAYMENT
# ==========================================================
@router.get("/verify/{reference}")
def verify_payment(reference: str):

    print("🔎 VERIFY:", reference)

    tx = transactions_collection.find_one({"reference": reference})

    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if tx["status"] == "success":
        return {
            "status": "already_verified",
            "balance": get_wallet_balance(tx["user_id"]),
        }

    response = requests.get(
        f"{PAYSTACK_VERIFY_URL}{reference}",
        headers=HEADERS,
    )

    data = response.json()

    if not data.get("status"):
        raise HTTPException(status_code=400, detail="Verification failed")

    paystack_data = data["data"]

    if paystack_data["status"] != "success":
        raise HTTPException(status_code=400, detail="Payment not successful")

    amount = paystack_data["amount"] / 100
    user_id = tx["user_id"]   # ✅ TRUST DB, NOT PAYSTACK

    print("✅ CREDIT USER:", user_id)

    # ======================================================
    # ✅ FIXED WALLET CREDIT (CONSISTENT FIELD)
    # ======================================================
    wallet = wallets_collection.find_one_and_update(
        {"user_id": user_id},   # ✅ FIXED (NOT _id)
        {
            "$inc": {"balance": amount},
            "$setOnInsert": {
                "user_id": user_id,
                "created_at": datetime.utcnow(),
            },
            "$set": {
                "updated_at": datetime.utcnow(),
            },
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )

    # ======================================================
    # UPDATE TRANSACTION
    # ======================================================
    transactions_collection.update_one(
        {"reference": reference},
        {
            "$set": {
                "status": "success",
                "balance_after": wallet["balance"],
                "updated_at": datetime.utcnow(),
            }
        },
    )

    print(f"✅ Wallet credited ₦{amount} | user={user_id}")

    return {
        "status": "success",
        "amount": amount,
        "balance": wallet["balance"],
    }

# ==========================================================
# HELPER
# ==========================================================
def get_wallet_balance(user_id: str):
    wallet = wallets_collection.find_one({"user_id": user_id})
    return wallet["balance"] if wallet else 0.0