from fastapi import APIRouter, Depends
from dependencies.auth import get_current_user
from core.config import HEADERS
import requests



from models.schemas import BuyCableRequest, VerifyCableRequest
from services.cable_service import (
    get_cable_plans_service,
    get_cable_providers_service,
    verify_cable_service,
    buy_cable_service,
)

router = APIRouter(prefix="/cable", tags=["Cable"])

# ================= GET PLANS =================
@router.get("/plans")
def get_plans(service: str, user=Depends(get_current_user)):
    return get_cable_plans_service(service)

# ================= BUY =================
@router.post("/buy")
def buy(req: BuyCableRequest, user=Depends(get_current_user)):
    return buy_cable_service(req, user)

@router.post("/verify", operation_id="verify_cable_tv")
def verify(req: VerifyCableRequest, user=Depends(get_current_user)):
    return verify_cable_service(req)




@router.get("/providers")
def get_providers(user=Depends(get_current_user)):
    return get_cable_providers_service()