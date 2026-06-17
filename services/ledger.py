from datetime import datetime
from db import transactions_collection

def log_transaction(user_id, amount, reference, tx_type, title):
    transactions_collection.insert_one({
        "user_id": user_id,
        "reference": reference,
        "amount": amount,
        "type": tx_type,  # credit or debit
        "title": title,
        "status": "success",
        "date": datetime.utcnow()
    })