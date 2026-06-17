from datetime import datetime
from db.db import transactions_collection

def resolve_vtpass_status(vt):
    code = str(vt.get("code", "")).strip()
    desc = vt.get("response_description", "").strip().upper()

    if code == "000":
        return "success"
    elif desc in ["TRANSACTION PENDING", "PROCESSING", "INITIATED"]:
        return "pending"
    return "failed"

 #============================================================
# 💾 SAVE TRANSACTION (CENTRALIZED)
# ============================================================
# def save_transaction(
#     user_id,
#     reference,
#     service,
#     amount,
#     status,
#     payload=None,
# ):
def save_transaction(
    user_id,
    reference,
    service,
    amount,
    status,
    transaction_type="debit",
    payload=None,
):
    # transaction = {
    #     "user_id": user_id,
    #     "reference": reference,
    #     "service": service,
    #     "amount": amount,
    #     "status": status,  # pending | success | failed
    #     "payload": payload or {},
    #     "created_at": datetime.utcnow(),
    #     "updated_at": datetime.utcnow(),
    # }
    transaction = {
    "user_id": user_id,
    "reference": reference,
    "service": service,
    "amount": amount,
    "type": transaction_type,
    "status": status,
    "payload": payload or {},
    "created_at": datetime.utcnow(),
    "updated_at": datetime.utcnow(),
}

    transactions_collection.insert_one(transaction)

    return transaction