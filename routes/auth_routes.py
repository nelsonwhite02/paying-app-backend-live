from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.db import users_collection, wallets_collection
from services.auth_jwt import create_access_token
from datetime import datetime
from fastapi import Depends
from dependencies.auth import get_current_user
from bson import ObjectId
import random

referral_code = f"PAY{random.randint(100000,999999)}"


router = APIRouter(prefix="/auth", tags=["Auth"])


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class UpdateProfileRequest(BaseModel):
    full_name: str
    phone: str
    address: str
    state: str

class ChangePinRequest(BaseModel):
    current_pin: str
    new_pin: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    phone: str
    full_name: str
    address: str
    state: str
    password: str
    pin: str
    referrer: str | None = None

class ResetPinRequest(BaseModel):
    password: str
    new_pin: str


@router.post("/register")
def register(data: RegisterRequest):

    # ==========================
    # CHECK EMAIL
    # ==========================
    existing_email = users_collection.find_one({
        "email": data.email
    })

    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    # ==========================
    # CHECK USERNAME
    # ==========================
    existing_username = users_collection.find_one({
        "username": data.username
    })

    if existing_username:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    # ==========================
    # CREATE USER
    # ==========================
    user = {
        "username": data.username,
        "email": data.email,
        "phone": data.phone,
        "full_name": data.full_name,
        "address": data.address,
        "state": data.state,
        "password": data.password,
        "pin": data.pin,
        "referral_code": referral_code,
        "referrer": data.referrer,
        "referral_count": 0,
        "referral_earnings": 0,
        "referral_rewarded": False,
        "kyc_tier": 1,   
        "created_at": datetime.utcnow()
    }

    result = users_collection.insert_one(user)

    user_id = str(result.inserted_id)

    # ==========================
    # CREATE WALLET
    # ==========================
    wallets_collection.insert_one({
        "user_id": user_id,
        "balance": 0.0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })

    # ==========================
    # GENERATE JWT
    # ==========================
    token = create_access_token({
        "user_id": user_id,
        "email": data.email
    })

    return {
        "message": "Account created successfully",
        "access_token": token,
        "token_type": "bearer",
        "user_id": user_id,
        "email": data.email
    }

class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(data: LoginRequest):

    user = users_collection.find_one({"email": data.email})

    if not user or user["password"] != data.password:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # ✅ Generate JWT
    token = create_access_token({
        "user_id": str(user["_id"]),
        "email": user["email"]
    })

    # ✅ RETURN FLAT RESPONSE (BEST PRACTICE)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": str(user["_id"]),
        "email": user["email"]
    }


@router.get("/profile")
def get_profile(user=Depends(get_current_user)):

    token_user_id = user.get("user_id") or user.get("_id")

    if not token_user_id:
        raise HTTPException(status_code=401, detail="Invalid user session credentials")

    try:
        # 2. Query using '_id' wrapped in ObjectId() since your schema uses standard MongoDB IDs
        db_user = users_collection.find_one(
            {"_id": ObjectId(token_user_id)},
            {"password": 0, "pin": 0}
        )

    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    # 3. Handle missing user
    if not db_user:
        raise HTTPException(status_code=404, detail="User profile not found")


    # db_user = users_collection.find_one(
    #     {"user_id": user["user_id"]},
    #     {"password": 0, "pin": 0}
    # )

    # if not db_user:
    #     raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": str(db_user["_id"]),
        "username": db_user.get("username"),
        "full_name": db_user.get("full_name"),
        "email": db_user.get("email"),
        "phone": db_user.get("phone"),
        "address": db_user.get("address"),
        "state": db_user.get("state"),
        "referrer": db_user.get("referrer"),
        "kyc_tier": db_user.get("kyc_tier", 1),
        "referral_code": db_user.get("referral_code", ""),
        "referred_by": db_user.get("referred_by"),
        "referral_count": db_user.get("referral_count", 0),
        "referral_earnings": db_user.get("referral_earnings", 0),
        "created_at": str(db_user.get("created_at")),
    }



@router.put("/profile")
def update_profile(
    data: UpdateProfileRequest,
    user=Depends(get_current_user)
):
    token_user_id = user.get("user_id") or user.get("_id")
    users_collection.update_one(
        {"_id": ObjectId(token_user_id)},
        {
            "$set": {
                "full_name": data.full_name,
                "phone": data.phone,
                "address": data.address,
                "state": data.state,
            }
        }
    )

    return {
        "message": "Profile updated successfully"
    }

@router.put("/change-password")
def change_password(
    data: ChangePasswordRequest,
    user=Depends(get_current_user)
):
    
    db_user = users_collection.find_one(
    {"_id": ObjectId(user["user_id"])}
    )                          
    

    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if db_user["password"] != data.current_password:
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect"
        )

    users_collection.update_one(
        {"_id": db_user["_id"]},
        {
            "$set": {
                "password": data.new_password
            }
        }
    )

    return {
        "message": "Password updated successfully"
    }


@router.put("/change-pin")
def change_pin(
    data: ChangePinRequest,
    user=Depends(get_current_user)
):

    db_user = users_collection.find_one(
        {"_id": ObjectId(user["user_id"])}
    )

    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if db_user.get("pin") != data.current_pin:
        raise HTTPException(
            status_code=400,
            detail="Current PIN is incorrect"
        )

    users_collection.update_one(
        {"_id": db_user["_id"]},
        {
            "$set": {
                "pin": data.new_pin
            }
        }
    )

    return {
        "message": "Transaction PIN updated successfully"
    }


@router.put("/forgot-pin")
def forgot_pin(
    data: ResetPinRequest,
    user=Depends(get_current_user)
):

    db_user = users_collection.find_one(
        {"_id": ObjectId(user["user_id"])}
    )

    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Verify password
    if db_user["password"] != data.password:
        raise HTTPException(
            status_code=400,
            detail="Incorrect password"
        )

    users_collection.update_one(
        {"_id": db_user["_id"]},
        {
            "$set": {
                "pin": data.new_pin
            }
        }
    )

    return {
        "message":
            "Transaction PIN reset successfully"
    }

def generate_referral_code(username: str):

    suffix = random.randint(
        1000,
        9999
    )

    return f"{username.upper()}{suffix}"