from jose import JWTError, jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv

import os


load_dotenv() 

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
SECRET_KEY = JWT_SECRET_KEY
print("JWT SECRET KEY:", SECRET_KEY, type(SECRET_KEY))
# SECRET_KEY = "your_super_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None