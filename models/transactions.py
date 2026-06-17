class Transaction:
    reference: str
    user_id: str
    amount: float
    status: str  # pending | success | failed
    type: str    # funding | debit | refund