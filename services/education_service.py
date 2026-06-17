import os
from datetime import datetime

from db.db import wallets_collection, transactions_collection
from services.vtpass_service import vtpass_query, vtpass_pay
from services.transaction_utils import resolve_vtpass_status
import requests
from core.config import HEADERS


# =========================================================
# 🎓 GET EDUCATION PLANS
# =========================================================
def get_education_plans_service(service: str):

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
# 🎓 BUY EDUCATION
# =========================================================
def buy_education_service(req, user):

    user_id = user["user_id"]
    service_id = req.service.lower()

    # ================= FETCH VARIATIONS =================
    vt_plans = vtpass_query(service_id)
    variations = vt_plans.get("content", {}).get("variations", [])

    selected = next(
        (v for v in variations if v["variation_code"] == req.variation_code),
        None
    )

    if not selected:
        return {"status": "failed", "message": "Invalid variation"}

    amount = float(selected["variation_amount"])
    total_amount = amount * req.quantity

    # ================= WALLET CHECK =================
    wallet = wallets_collection.find_one({"user_id": user_id})

    if not wallet or wallet.get("balance", 0) < total_amount:
        return {"status": "failed", "message": "Insufficient funds"}

    # ================= DEBIT =================
    
    reference = "edu_" + os.urandom(6).hex()
   
    wallets_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"balance": -total_amount}}
    )

    # ================= VTPASS =================
    payload = {
        "request_id": reference,
        "serviceID": service_id,
        "billersCode": req.phone,
        "variation_code": req.variation_code,
        "amount": total_amount,
        "phone": req.phone,
        "quantity": req.quantity
    }

    vt = vtpass_pay(payload)

    print("🎓 VT RESPONSE:", vt)
    
    status = resolve_vtpass_status(vt)

    # ================= EXTRACT PIN =================
    pin = (
    vt.get("purchased_code")
    or vt.get("pin")
    or ""
    )

    cards = vt.get("cards", [])

    # ================= SAVE =================
    result = transactions_collection.insert_one({
    "user_id": user_id,
    "reference": reference,
    "amount": total_amount,
    "type": "debit",
    "service": req.service,
    "phone": req.phone,
    "plan_name": selected.get("name"),
    "quantity": req.quantity,
    "pin": pin,
    "cards": cards,
    "status": status,
    "created_at": datetime.utcnow()
    })
    print("✅ EDUCATION SAVED:", result.inserted_id)

    # ================= HANDLE =================
    if status == "success":
        return {
            "status": "success",
            "reference": reference,
            "pin": pin,
            "quantity": req.quantity,
            "exam_type": selected.get("name")
        }

    elif status == "pending":
        return {
            "status": "pending",
            "reference": reference,
            "message": "Exam PIN is being processed"
        }

    else:
        # REFUND
        wallets_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"balance": total_amount}}
        )

        return {
            "status": "failed",
            "reference": reference,
            "message": vt.get(
                "response_description",
                "Transaction failed"
            )
        }




# =========================================================
# 🎓 GET EDUCATION SERVICES
# =========================================================
# =========================================================
# 🎓 GET EDUCATION SERVICES
# =========================================================
def get_education_services_service():

    return {
        "status": "success",
        "services": [
            {
                "serviceID": "waec",
                "name": "WAEC Result Checker"
            },
            {
                "serviceID": "waec-registration",
                "name": "WAEC Registration"
            },
            {
                "serviceID": "neco",
                "name": "NECO Token"
            },
            {
                "serviceID": "jamb",
                "name": "JAMB ePIN"
            },
            {
                "serviceID": "nabteb",
                "name": "NABTEB PIN"
            }
        ]
    }




# def get_education_services_service():

#     available = []

#     for service in EDUCATION_SERVICES:

#         try:
#             response = vtpass_query(service["serviceID"])

#             plans = response.get(
#                 "content",
#                 {}
#             ).get(
#                 "variations",
#                 []
#             )

#             if plans:
#                 available.append(service)

#         except Exception:
#             pass

#     return {
#         "status": "success",
#         "services": available
#     }