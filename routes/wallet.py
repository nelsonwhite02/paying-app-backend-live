from fastapi import APIRouter, HTTPException, Depends
from pymongo import MongoClient
from db.db import wallets_collection,transactions_collection
from datetime import datetime
from pymongo import ReturnDocument

from db import db
from dependencies.auth import get_current_user

router = APIRouter(prefix="/wallet", tags=["Wallet"])


# ==========================================================
# GET WALLET BALANCE (JWT SECURED)
# ==========================================================
@router.get("/")
def get_wallet(user=Depends(get_current_user)):
    user_id = user["user_id"]

    wallet = wallets_collection.find_one({"user_id": user_id})

    if not wallet:
        # auto-create wallet if not exists
        wallets_collection.insert_one({
            "user_id": user_id,
            "balance": 0.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })

        return {
            "user_id": user_id,
            "balance": 0.0,
        }

    return {
        "user_id": user_id,
        "balance": float(wallet.get("balance", 0.0)),
    }


# ==========================================================
# CREDIT WALLET (IDEMPOTENT & SAFE)
# ==========================================================
def credit_wallet(user_id: str, amount: float, reference: str):

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid credit amount")

    # ------------------------------------------------------
    # 1️⃣ CHECK TRANSACTION (IDEMPOTENCY)
    # ------------------------------------------------------
    existing_tx = transactions_collection.find_one({
        "reference": reference
    })

    if existing_tx and existing_tx.get("status") == "success":
        return {
            "status": "ignored",
            "message": "Transaction already processed",
            "balance": _get_wallet_balance(user_id),
        }

    # ------------------------------------------------------
    # 2️⃣ CREDIT WALLET (ATOMIC)
    # ------------------------------------------------------
    wallet = wallets_collection.find_one_and_update(
        {"user_id": user_id},
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
        return_document=ReturnDocument.AFTER,  # ✅ FIXED
    )

    new_balance = float(wallet.get("balance", 0.0))

    # ------------------------------------------------------
    # 3️⃣ SAVE TRANSACTION (LEDGER)
    # ------------------------------------------------------
    transactions_collection.update_one(
        {"reference": reference},
        {
            "$set": {
                "user_id": user_id,
                "reference": reference,
                "amount": amount,
                "type": "credit",
                "title": "Wallet Funding",
                "network": "",
                "phone": "",
                "plan_name": "",
                "status": "success",
                "date": datetime.utcnow(),
                "balance_after": new_balance,
                "updated_at": datetime.utcnow(),
            },
            "$setOnInsert": {
                "created_at": datetime.utcnow(),
            },
        },
        upsert=True,
    )

    return {
        "status": "success",
        "reference": reference,
        "credited_amount": amount,
        "balance": new_balance,
    }


# ==========================================================
# DEBIT WALLET
# ==========================================================
def debit_wallet(user_id: str, amount: float):

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid debit amount")

    wallet = wallets_collection.find_one({"user_id": user_id})

    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    balance = float(wallet.get("balance", 0.0))

    if balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    new_balance = balance - amount

    wallets_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "balance": new_balance,
                "updated_at": datetime.utcnow(),
            }
        }
    )

    return new_balance


# ==========================================================
# GET TRANSACTION HISTORY (JWT SECURED)
# ==========================================================
@router.get("/transactions")
def get_transactions(user=Depends(get_current_user)):
    user_id = user["user_id"]

    transactions_cursor = transactions_collection.find(
        {"user_id": user_id}
    ).sort("date", -1)

    transactions = []

    for tx in transactions_cursor:
        tx["_id"] = str(tx["_id"])
        transactions.append(tx)

    return {
        "transactions": transactions
    }


# ==========================================================
# INTERNAL HELPER
# ==========================================================
def _get_wallet_balance(user_id: str) -> float:
    wallet = wallets_collection.find_one({"user_id": user_id})
    return float(wallet.get("balance", 0.0)) if wallet else 0.0

# client = MongoClient("mongodb://localhost:27017")
# db = client["paying_app"]

# wallets = db["wallets"]

# @router.get("/{user_id}")
# def get_wallet_balance(user_id: str):
#     wallet = wallets_collection.find_one({"user_id": user_id})

#     if not wallet:
#         return {"balance": 0}

#     return {
#         "balance": wallet.get("balance", 0)
#     }
