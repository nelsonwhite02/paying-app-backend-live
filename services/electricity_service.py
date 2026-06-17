import os
from datetime import datetime
from unittest import result

from db.db import wallets_collection, transactions_collection
from services.vtpass_service import vtpass_pay
from services.transaction_utils import resolve_vtpass_status
import requests
from core.config import HEADERS


# =========================================================
# ⚡ VERIFY METER
# =========================================================
def verify_meter_service(req):

    import requests
    from core.config import HEADERS

    payload = {
        "billersCode": req.meter_number,
        "serviceID": req.service,
        "type": req.meter_type,
    }

    res = requests.post(
        "https://sandbox.vtpass.com/api/merchant-verify",
        json=payload,
        headers=HEADERS,
        timeout=20
    )

    data = res.json()
    print("⚡ VERIFY RESPONSE:", data)

    if data.get("code") != "000":
        return {
            "status": "failed",
            "message": data.get("response_description", "Verification failed")
        }

    return {
        "status": "success",
        "customer_name": data["content"]["Customer_Name"],
        "address": data["content"].get("Address", "")
    }


# =========================================================
# ⚡ BUY ELECTRICITY
# =========================================================
def buy_electricity_service(req, user):

    user_id = user["user_id"]
    amount = float(req.amount)

    if amount <= 0:
        return {"status": "failed", "message": "Invalid amount"}

    # ================= WALLET CHECK =================
    wallet = wallets_collection.find_one({"user_id": user_id})

    if not wallet or wallet.get("balance", 0) < amount:
        return {"status": "failed", "message": "Insufficient funds"}

    # ================= DEBIT =================
    reference = "elec_" + os.urandom(6).hex()

    wallets_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"balance": -amount}}
    )

    # ================= VTPASS CALL =================
    payload = {
        "request_id": reference,
        "serviceID": req.service,
        "billersCode": req.meter_number,
        "variation_code": req.meter_type,
        "amount": amount,
        "phone": req.phone
    }

    vt = vtpass_pay(payload)

    print("⚡ VT RESPONSE:", vt)

    status = resolve_vtpass_status(vt)

    # ================= EXTRACT TOKEN =================
    token = (
        vt.get("purchased_code") or
        vt.get("content", {}).get("transactions", {}).get("token")
    )

    units = (
    vt.get("units")
    or vt.get("content", {})
         .get("transactions", {})
         .get("units")
    )
    # ================= SAVE =================
    result =transactions_collection.insert_one({
        "user_id": user_id,
        "reference": reference,
        "amount": amount,
        "type": "debit",
        "service": req.service,
        "meter_number": req.meter_number,
        "meter_type": req.meter_type,
        "token": token,
        "units": units,
        "status": status,
        "created_at": datetime.utcnow()
    })
    print("✅ SAVED:", result.inserted_id)
    # ================= HANDLE STATES =================

    if status == "success":
        return {
            "status": "success",
            "reference": reference,
            "token": token,
            "units": units,
            "meter_number": req.meter_number,
            "outstanding": vt.get("debtAmount", 0),
        }

    elif status == "pending":
        return {
            "status": "pending",
            "reference": reference,
            "message": "Transaction is processing"
        }

    else:
        # ❌ FAILED → REFUND
        wallets_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"balance": amount}}
        )

        return {
            "status": "failed",
            "reference": reference,
            "message": vt.get("response_description", "Transaction failed")
        }



def get_electricity_providers_service():

    response = requests.get(
        "https://sandbox.vtpass.com/api/services?identifier=electricity-bill",
        headers=HEADERS,
        timeout=20
    )

    data = response.json()

    return data