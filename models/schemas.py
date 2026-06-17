from pydantic import BaseModel

class BuyAirtimeRequest(BaseModel):
    network: str
    phone: str
    amount: float


class BuyDataRequest(BaseModel):
    network: str
    phone: str
    variation_code: str


class BuyCableRequest(BaseModel):
    service: str
    smartcard_number: str
    variation_code: str
    phone: str


class BuyElectricityRequest(BaseModel):
    service: str
    meter_number: str
    meter_type: str
    amount: float
    phone: str


class BuyEducationRequest(BaseModel):
    service: str
    variation_code: str
    phone: str
    quantity: int = 1


class VerifyCableRequest(BaseModel):
    service: str
    smartcard_number: str


class VerifyMeterRequest(BaseModel):
    service: str
    meter_number: str
    meter_type: str

