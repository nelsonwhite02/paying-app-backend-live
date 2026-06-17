from fastapi import Header, HTTPException,Depends, HTTPException
from services.auth_jwt import verify_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import os
from dotenv import load_dotenv


load_dotenv() 

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
SECRET_KEY = JWT_SECRET_KEY
ALGORITHM = "HS256"

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        return {
            "user_id": payload.get("user_id"),
            "email": payload.get("email")
        }

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# def get_current_user(authorization: str = Header(None)):
#     if not authorization:
#         raise HTTPException(status_code=401, detail="No token provided")

#     try:
#         token = authorization.split(" ")[1]  # Bearer TOKEN
#     except:
#         raise HTTPException(status_code=401, detail="Invalid token format")

#     payload = verify_token(token)

#     if not payload:
#         raise HTTPException(status_code=401, detail="Invalid or expired token")

#     return payload  # contains user_id