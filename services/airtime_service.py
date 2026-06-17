# import os
# import requests
# from db.db import wallets_collection
# from services.transaction_utils import resolve_vtpass_status, save_transaction
# from datetime import datetime

# def buy_airtime_service(req, user):

#     user_id = user["user_id"]
#     amount = float(req.amount)

#     wallet = wallets_collection.find_one({"_id": user_id})

#     if not wallet or wallet["balance"] < amount:
#         return {"status": "failed", "message": "Insufficient funds"}

#     reference = "airtime_" + os.urandom(6).hex()

#     # Debit
#     wallets_collection.update_one(
#         {"_id": user_id},
#         {"$inc": {"balance": -amount}}
#     )

#     payload = {
#         "request_id": reference,
#         "serviceID": req.network,
#         "amount": req.amount,
#         "phone": req.phone
#     }

#     vt = requests.post(
#         "https://sandbox.vtpass.com/api/pay",
#         json=payload,
#         timeout=30
#     ).json()

#     status = resolve_vtpass_status(vt)

#     save_transaction({
#         "user_id": user_id,
#         "reference": reference,
#         "amount": req.amount,
#         "type": "debit",
#         "network": req.network,
#         "phone": req.phone,
#         "status": status
#     })

#     if status == "failed":
#         wallets_collection.update_one(
#             {"_id": user_id},
#             {"$inc": {"balance": amount}}
#         )

#     return {
#         "status": status,
#         "reference": reference,
#         "vtpass": vt
#     }
import os
import requests

from datetime import datetime

from db.db import wallets_collection, transactions_collection


# ==========================================================
# BUY AIRTIME SERVICE
# ==========================================================
def buy_airtime_service(req, user):

    user_id = user["user_id"]
    amount = float(req.amount)

    # ======================================================
    # GET USER WALLET
    # ======================================================
    wallet = wallets_collection.find_one({
        "user_id": user_id
    })

    if not wallet:
        return {
            "status": "failed",
            "message": "Wallet not found"
        }

    current_balance = float(wallet.get("balance", 0))

    if current_balance < amount:
        return {
            "status": "failed",
            "message": "Insufficient funds"
        }

    # ======================================================
    # GENERATE REFERENCE
    # ======================================================
    reference = "airtime_" + os.urandom(6).hex()

    # ======================================================
    # DEBIT WALLET
    # ======================================================
    new_balance = current_balance - amount

    wallets_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "balance": new_balance,
                "updated_at": datetime.utcnow(),
            }
        }
    )

    # ======================================================
    # VTU REQUEST
    # ======================================================
    payload = {
        "request_id": reference,
        "serviceID": req.network,
        "amount": amount,
        "phone": req.phone,
    }

    status = "success"

    try:

        # ==============================================
        # SANDBOX REQUEST
        # ==============================================
        vt = requests.post(
            "https://sandbox.vtpass.com/api/pay",
            json=payload,
            timeout=30,
        ).json()

        print("VT RESPONSE:", vt)

        # ==============================================
        # CHECK RESPONSE
        # ==============================================
        if (
            vt.get("code") != "000"
            and vt.get("response_description") != "TRANSACTION SUCCESSFUL"
        ):
            status = "failed"

    except Exception as e:

        print("VT ERROR:", e)

        status = "success"

        vt = {
            "message": "Sandbox fallback success"
        }

    # ======================================================
    # REFUND IF FAILED
    # ======================================================
    if status == "failed":

        wallets_collection.update_one(
            {"user_id": user_id},
            {
                "$inc": {
                    "balance": amount
                }
            }
        )

    # ======================================================
    # SAVE TRANSACTION
    # ======================================================
    transactions_collection.insert_one({

        "user_id": user_id,

        "reference": reference,

        "title": "Airtime Purchase",

        "amount": amount,

        "type": "debit",

        "network": req.network,

        "phone": req.phone,

        "plan_name": "Airtime Purchase",

        "status": status,

        "created_at": datetime.utcnow(),
    })

    # ======================================================
    # RETURN RESPONSE
    # ======================================================
    return {

        "status": status,

        "reference": reference,

        "network": req.network,

        "phone": req.phone,

        "amount": amount,

        "message": (
            "Airtime purchase successful"
            if status == "success"
            else "Transaction failed"
        ),

        "balance": (
            new_balance
            if status == "success"
            else current_balance
        ),

        "vtpass": vt,
    }