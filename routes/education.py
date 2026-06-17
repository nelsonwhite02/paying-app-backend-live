from fastapi import APIRouter, Depends
from dependencies.auth import get_current_user

from models.schemas import BuyEducationRequest
from services.education_service import (
    get_education_plans_service,
    buy_education_service,
    get_education_services_service,
    
)

router = APIRouter(prefix="/education", tags=["Education"])


# =========================================================
# 🎓 GET EDUCATION SERVICES
# =========================================================
@router.get("/services")
def get_services(user=Depends(get_current_user)):
    return get_education_services_service()

# ================= GET PLANS =================
@router.get("/plans")
def get_plans(service: str, user=Depends(get_current_user)):
    return get_education_plans_service(service)

# ================= BUY =================
@router.post("/buy")
def buy(req: BuyEducationRequest, user=Depends(get_current_user)):
    return buy_education_service(req, user)