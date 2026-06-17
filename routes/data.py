from fastapi import APIRouter, Depends, Query, HTTPException
from models.schemas import BuyDataRequest
from dependencies.auth import get_current_user
from services.data_service import buy_data_service

import requests
import os

router = APIRouter(tags=["Data"])

# ======================================================
# VT PASS CONFIG
# ======================================================

VT_PASS_API_KEY = os.getenv("VT_PASS_API_KEY", "sandbox")
VT_PASS_SECRET_KEY = os.getenv("VT_PASS_SECRET_KEY", "sandbox")

HEADERS = {
    "api-key": VT_PASS_API_KEY,
    "secret-key": VT_PASS_SECRET_KEY,
    "Content-Type": "application/json",
}

# ======================================================
# 📶 BUY DATA
# ======================================================

@router.post("/buy-data")
def buy_data(
    req: BuyDataRequest,
    user=Depends(get_current_user)
):
    return buy_data_service(req, user)

# ======================================================
# 📶 DATA PLANS
# ======================================================

@router.get("/data-plans")
def get_data_plans(
    network: str = Query(
        ...,
        description="mtn, glo, airtel, 9mobile"
    ),
    user=Depends(get_current_user)
):
    try:

        service_id = f"{network.lower()}-data"

        # print(f"📶 Fetching data plans for {service_id}")

        response = requests.get(
            "https://sandbox.vtpass.com/api/service-variations",
            params={"serviceID": service_id},
            headers=HEADERS,
            timeout=20
        )

        data = response.json()

        # print("📶 VT PASS RESPONSE:", data)

        # ==================================================
        # VALIDATION
        # ==================================================

        if (
            "content" not in data or
            "variations" not in data["content"]
        ):
            raise HTTPException(
                status_code=500,
                detail="Invalid response from VTpass"
            )

        variations = data["content"]["variations"]

        # ==================================================
        # RESPONSE
        # ==================================================

        return {
            "status": "success",
            "content": {
                "variations": [
                    {
                        "variation_code": v.get("variation_code"),
                        "name": v.get("name"),
                        "variation_amount": v.get("variation_amount"),
                    }
                    for v in variations
                ]
            }
        }

    except Exception as e:

        # print("🔥 DATA PLAN ERROR:", str(e))

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )