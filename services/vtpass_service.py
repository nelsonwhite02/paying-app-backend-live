import os
import requests
from datetime import datetime
from fastapi import HTTPException
from db.db import wallets_collection, transactions_collection
import requests
from core.config import HEADERS
from dotenv import load_dotenv



load_dotenv() 

VT_BASE_URL = "https://sandbox.vtpass.com/api"

# ======================================================
# 🔐 VTpass KEYS
# ======================================================

VT_API_KEY = os.getenv("VT_API_KEY")
VT_PUBLIC_KEY = os.getenv("VT_PUBLIC_KEY")
VT_SECRET_KEY = os.getenv("VT_SECRET_KEY")

HEADERS = {
    "api-key": VT_API_KEY,
    "public-key": VT_PUBLIC_KEY,
    "secret-key": VT_SECRET_KEY,
    "Content-Type": "application/json",
}




def vtpass_pay(payload):
    return requests.post(
        "https://sandbox.vtpass.com/api/pay",
        json=payload,
        headers=HEADERS,
        timeout=30
    ).json()

def vtpass_query(service_id):
    return requests.get(
        "https://sandbox.vtpass.com/api/service-variations",
        params={"serviceID": service_id},
        headers=HEADERS,
        timeout=20
    ).json()

def process_vtpass_payment(
    user_id: str,
    service_id: str,
    billers_code: str,
    variation_code: str,
    phone: str,
    amount: float,
    extra: dict = {}
):
    # 1️⃣ CHECK & DEBIT WALLET (ATOMIC)
    wallet = wallets_collection.find_one_and_update(
        {"_id": user_id, "balance": {"$gte": amount}},
        {"$inc": {"balance": -amount}},
    )

    if not wallet:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    reference = "tx_" + os.urandom(6).hex()

    # 2️⃣ CALL VTPASS
    payload = {
        "request_id": reference,
        "serviceID": service_id,
        "billersCode": billers_code,
        "variation_code": variation_code,
        "amount": amount,
        "phone": phone,
        **extra
    }

    response = requests.post(
            "https://sandbox.vtpass.com/api/pay",
            json=payload,
            headers=HEADERS,
            timeout=30
        )

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="VTpass error")

    vt = response.json()

    code = str(vt.get("code", "")).strip()
    desc = vt.get("response_description", "").upper()

    is_success = code == "000" or desc == "TRANSACTION SUCCESSFUL"

    # ================= SUCCESS =================
    if is_success:
        transactions_collection.insert_one({
            "user_id": user_id,
            "reference": reference,
            "amount": amount,
            "type": "debit",
            "service": service_id,
            "phone": phone,
            "status": "success",
            "created_at": datetime.utcnow()
        })

        return {"status": "success", "data": vt}

    # ================= FAILURE =================
    wallets_collection.update_one(
        {"_id": user_id},
        {"$inc": {"balance": amount}}
    )

    transactions_collection.insert_one({
        "user_id": user_id,
        "reference": reference,
        "amount": amount,
        "type": "debit",
        "service": service_id,
        "phone": phone,
        "status": "failed",
        "created_at": datetime.utcnow()
    })

    return {"status": "failed", "data": vt}