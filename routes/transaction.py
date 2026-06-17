from fastapi import APIRouter
from db.db import transactions_collection

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)


@router.get("/{reference}")
def get_transaction(reference: str):

    txn = transactions_collection.find_one(
        {"reference": reference}
    )

    if not txn:
        return {
            "status": "failed",
            "message": "Transaction not found"
        }

    return {
        "status": txn.get("status"),
        "reference": txn.get("reference"),
        "amount": txn.get("amount"),
        "pin": txn.get("pin"),
        "cards": txn.get("cards", []),
        "service": txn.get("service"),
        "phone": txn.get("phone"),
        "plan_name": txn.get("plan_name"),
        "quantity": txn.get("quantity")
    }