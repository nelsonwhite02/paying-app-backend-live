import os
from datetime import datetime

from db.db import wallets_collection, transactions_collection
from services.vtpass_service import vtpass_query, vtpass_pay
from services.transaction_utils import resolve_vtpass_status
from core.config import HEADERS
import requests


# =========================================================
# 📺 GET CABLE PLANS
# =========================================================
def get_cable_plans_service(service: str):

    vt = vtpass_query(service)

    variations = vt.get("content", {}).get("variations", [])

    return {
        "plans": [
            {
                "variation_code": v.get("variation_code"),
                "name": v.get("name"),
                "amount": v.get("variation_amount"),
            }
            for v in variations
        ]
    }


# =========================================================
# 📺 VERIFY SMARTCARD
# =========================================================
def verify_cable_service(req):

    import requests
    from core.config import HEADERS

    payload = {
        "billersCode": req.smartcard_number,
        "serviceID": req.service,
    }

    res = requests.post(
        "https://sandbox.vtpass.com/api/merchant-verify",
        json=payload,
        headers=HEADERS,
        timeout=20
    )

    data = res.json()
    print("📺 VERIFY RESPONSE:", data)

    if data.get("code") != "000":
        return {
            "status": "failed",
            "message": data.get("response_description", "Verification failed")
        }

    return {
        "status": "success",
        "customer_name": data["content"]["Customer_Name"]
    }


# =========================================================
# 📺 BUY CABLE
# =========================================================
def buy_cable_service(req, user):

    user_id = user["user_id"]

    # ================= FETCH PLANS =================
    vt_plans = vtpass_query(req.service)
    variations = vt_plans.get("content", {}).get("variations", [])

    selected = next(
        (v for v in variations if v["variation_code"] == req.variation_code),
        None
    )

    if not selected:
        return {"status": "failed", "message": "Invalid bouquet"}

    amount = float(selected["variation_amount"])

    # ================= WALLET CHECK =================
    wallet = wallets_collection.find_one({"user_id": user_id})

    if not wallet or wallet.get("balance", 0) < amount:
        return {"status": "failed", "message": "Insufficient funds"}

    # ================= DEBIT =================
    reference = "cable_" + os.urandom(6).hex()

    wallets_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"balance": -amount}}
    )

    # ================= VTPASS =================
    payload = {
        "request_id": reference,
        "serviceID": req.service,
        "billersCode": req.smartcard_number,
        "variation_code": req.variation_code,
        "amount": amount,
        "phone": req.phone
    }

    vt = vtpass_pay(payload)
    print("========== BUY CABLE ==========")
    print("USER:", user_id)
    print("SERVICE:", req.service)
    print("SMARTCARD:", req.smartcard_number)
    print("VARIATION:", req.variation_code)

    print("📺 VT RESPONSE:", vt)

    status = resolve_vtpass_status(vt)

    # ================= SAVE =================
    result= transactions_collection.insert_one({
        "user_id": user_id,
        "reference": reference,
        "amount": amount,
        "type": "debit",
        "service": req.service,
        "smartcard_number": req.smartcard_number,
        "variation_code": req.variation_code,
        "plan_name": selected.get("name"),
        "customer_name": vt.get("customerName"),
        "status": status,
        "created_at": datetime.utcnow()
    })
    print("✅ CABLE SAVED:", result.inserted_id)

    # ================= HANDLE =================
    if status == "success":
        return {
            "status": "success",
            "reference": reference,
            "smartcard_number": req.smartcard_number,
            "plan_name": selected.get("name"),
            "amount": amount,
            "customer_name": vt.get("customerName")
        }

    elif status == "pending":
        return {
            "status": "pending",
            "reference": reference,
            "message": "Subscription processing"
        }

    else:
        # REFUND
        wallets_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"balance": amount}}
        )

        return {
            "status": "failed",
            "reference": reference,
            "message": vt.get("response_description", "Transaction failed")
        }
    
# def get_cable_providers_service():

#     vt = vtpass_query("tv-subscription")

#     return vt

def get_cable_providers_service():

    response = requests.get(
        "https://sandbox.vtpass.com/api/services?identifier=tv-subscription",
        headers=HEADERS,
        timeout=20,
    )

    return response.json()