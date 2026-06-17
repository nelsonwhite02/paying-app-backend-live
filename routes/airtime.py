from fastapi import APIRouter, Depends
from models.schemas import BuyAirtimeRequest
from dependencies.auth import get_current_user
from services.airtime_service import buy_airtime_service

router = APIRouter(prefix="/airtime", tags=["Airtime"])

@router.post("/buy")
def buy_airtime(req: BuyAirtimeRequest, user=Depends(get_current_user)):
    return buy_airtime_service(req, user)