from fastapi import APIRouter
from db.db import db

router = APIRouter(prefix="/ledger", tags=["Ledger"])


@router.get("/{user_id}")
async def get_ledger(user_id: str):

    # GET TRANSACTIONS
    txs = list(
        db.transactions.find(
            {"user_id": user_id}
        ).sort("created_at", -1)
    )

    # CONVERT OBJECT IDS
    for tx in txs:
        tx["_id"] = str(tx["_id"])

    # CALCULATE TOTALS
    total_credit = sum(
        tx.get("amount", 0)
        for tx in txs
        if tx.get("type") == "credit"
    )

    total_debit = sum(
        tx.get("amount", 0)
        for tx in txs
        if tx.get("type") == "debit"
    )

    return {
        "status": "success",
        "total_credit": total_credit,
        "total_debit": total_debit,
        "transactions": txs,
        
    }