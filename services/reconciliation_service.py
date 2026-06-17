from db.db import transactions_collection, wallets_collection
from services.vtpass_status import check_vtpass_status


def reconcile_transactions():

    print("🔁 Running transaction reconciliation...")

    pending_txs = list(
        transactions_collection.find({"status": "pending"})
    )

    for tx in pending_txs:
        ref = tx.get("reference")

        print("🔍 Checking:", ref)

        result = check_vtpass_status(ref)

        # ================= SUCCESS =================
        if result["success"]:
            print("✅ CONFIRMED SUCCESS:", ref)

            transactions_collection.update_one(
                {"reference": ref},
                {"$set": {"status": "success"}}
            )

        # ================= STILL PENDING =================
        elif result["pending"]:
            print("⏳ STILL PENDING:", ref)
            continue

        # ================= FAILED =================
        else:
            print("❌ CONFIRMED FAILED:", ref)

            # REFUND WALLET
            wallets_collection.update_one(
                {"_id": tx["user_id"]},
                {"$inc": {"balance": tx["amount"]}}
            )

            transactions_collection.update_one(
                {"reference": ref},
                {"$set": {"status": "failed"}}
            )