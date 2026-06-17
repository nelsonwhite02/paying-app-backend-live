from fastapi import APIRouter, Depends
from dependencies.auth import get_current_user
from models.schemas import VerifyMeterRequest

from models.schemas import BuyElectricityRequest
from services.electricity_service import (
    verify_meter_service,
    buy_electricity_service
)

router = APIRouter(prefix="/electricity", tags=["Electricity"])

# ================= VERIFY METER =================
# @router.post("/verify", operation_id="verify_electricity_meter")
# def verify_meter(req: dict, user=Depends(get_current_user)):
#     return verify_meter_service(req)

# ================= BUY ELECTRICITY =================
@router.post("/buy")
def buy_electricity(req: BuyElectricityRequest, user=Depends(get_current_user)):
    return buy_electricity_service(req, user)

@router.post("/verify")
def verify_meter(req: VerifyMeterRequest, user=Depends(get_current_user)):
    return verify_meter_service(req)

# routes/electricity.py

@router.get("/providers")
def get_electricity_providers(user=Depends(get_current_user)):
    from services.electricity_service import get_electricity_providers_service
    return get_electricity_providers_service()