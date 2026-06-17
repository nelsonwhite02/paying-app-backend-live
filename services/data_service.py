import os
from db.db import wallets_collection
from services.vtpass_service import vtpass_pay, vtpass_query
from services.transaction_utils import resolve_vtpass_status, save_transaction


def buy_data_service(req, user):

    user_id = user["user_id"]

    service_id = f"{req.network.lower()}-data"

    # ================= FETCH PLANS =================
    vt_plans = vtpass_query(service_id)

    variations = vt_plans.get("content", {}).get("variations", [])

    selected = next(
        (v for v in variations if v["variation_code"] == req.variation_code),
        None
    )

    if not selected:
        return {"status": "failed", "message": "Invalid data plan"}

    amount = float(selected["variation_amount"])

    # ================= WALLET CHECK =================
    wallet = wallets_collection.find_one({"user_id": user_id})

    if not wallet or wallet.get("balance", 0) < amount:
        return {"status": "failed", "message": "Insufficient funds"}

    # ================= DEBIT =================
    reference = "data_" + os.urandom(6).hex()

    wallets_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"balance": -amount}}
    )

    # ================= CALL VTPASS =================
    payload = {
        "request_id": reference,
        "serviceID": service_id,
        "billersCode": req.phone,
        "variation_code": req.variation_code,
        "amount": amount,
        "phone": req.phone
    }

    vt = vtpass_pay(payload)

    print("📶 DATA VT RESPONSE:", vt)

    # ================= STATUS =================
    status = resolve_vtpass_status(vt)

    # ================= SAVE =================
    # save_transaction({
    #     "user_id": user_id,
    #     "reference": reference,
    #     "amount": amount,
    #     "type": "debit",
    #     "network": req.network,
    #     "phone": req.phone,
    #     "plan_name": selected.get("name"),
    #     "status": status
    # })
    save_transaction(
    user_id=user_id,
    reference=reference,
    service=service_id,
    amount=amount,
    status=status,
    transaction_type="debit",
    payload={
        "network": req.network,
        "phone": req.phone,
        "plan_name": selected.get("name"),
    }
)

    # ================= HANDLE STATES =================

    if status == "success":
        return {
            "status": "success",
            "reference": reference,
            "message": "Data purchase successful"
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