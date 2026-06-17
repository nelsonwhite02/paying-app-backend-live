from fastapi import FastAPI, Query, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
import threading
import time
from db.db import transactions_collection, wallets_collection
from dependencies.auth import get_current_user
from routes.ledger import router as ledger_router

# Routers
from routes import (
    auth_routes,
    wallet,
    paystack,
    airtime,
    data,
    cable,
    electricity,
    education,
)

# Background job
from services.reconciliation_service import reconcile_transactions

app = FastAPI(
    title="Paying App Backend",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/transactions/{reference}")
def get_transaction(reference: str, user=Depends(get_current_user)):

    tx = transactions_collection.find_one({
        "reference": reference,
        "user_id": user["user_id"]
    })

    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return {
        "status": tx.get("status"),
        "reference": reference,
        "amount": tx.get("amount"),
        "type": tx.get("type"),

        # electricity specific
        "token": tx.get("token"),
        "units": tx.get("units"),

        # optional
        "plan_name": tx.get("plan_name"),
        "service": tx.get("service"),
      
        "pin": tx.get("pin"),
        "cards": tx.get("cards", []),
        "service": tx.get("service"),
        "phone": tx.get("phone"),
        "plan_name": tx.get("plan_name"),
        "quantity": tx.get("quantity")
    }
# Health
@app.get("/")
def health():
    return {"status": "ok"}

# Routers
app.include_router(auth_routes.router)
app.include_router(wallet.router)
app.include_router(paystack.router)
app.include_router(airtime.router)
app.include_router(data.router)
app.include_router(cable.router)
app.include_router(electricity.router)
app.include_router(education.router)
app.include_router(ledger_router)

# Background reconciliation loop
def reconciliation_worker():
    while True:
        try:
            print("🔁 Running transaction reconciliation...")
            reconcile_transactions()
        except Exception as e:
            print("❌ Reconciliation error:", e)

        time.sleep(60)  # ✅ important


@app.on_event("startup")
def start_background_tasks():
    # ✅ prevent duplicate threads in dev reload
    if os.environ.get("RUN_MAIN") == "true":
        thread = threading.Thread(target=reconciliation_worker, daemon=True)
        thread.start()