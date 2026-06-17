from db.db import wallets_collection

def debit_wallet(user_id, amount):
    wallet = wallets_collection.find_one({"_id": user_id})

    if not wallet or wallet["balance"] < amount:
        return False

    wallets_collection.update_one(
        {"_id": user_id},
        {"$inc": {"balance": -amount}}
    )
    return True


def refund_wallet(user_id, amount):
    wallets_collection.update_one(
        {"_id": user_id},
        {"$inc": {"balance": amount}}
    )