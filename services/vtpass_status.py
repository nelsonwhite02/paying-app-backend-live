import requests
import os
from dotenv import load_dotenv

load_dotenv()

VT_API_KEY = os.getenv("VT_API_KEY")
VT_PUBLIC_KEY = os.getenv("VT_PUBLIC_KEY")
VT_SECRET_KEY = os.getenv("VT_SECRET_KEY")

HEADERS = {
    "api-key": VT_API_KEY,
    "public-key": VT_PUBLIC_KEY,
    "secret-key": VT_SECRET_KEY,
    "Content-Type": "application/json",
}

def check_vtpass_status(request_id: str):
    try:
        payload = {"request_id": request_id}

        response = requests.post(
            "https://sandbox.vtpass.com/api/requery",
            json=payload,
            headers=HEADERS,
            timeout=20
        )

        data = response.json()

        code = str(data.get("code", "")).strip()
        desc = data.get("response_description", "").upper()

        is_success = (
            code == "000" or
            desc == "TRANSACTION SUCCESSFUL"
        )

        is_pending = desc in [
            "TRANSACTION PENDING",
            "INITIATED",
            "PROCESSING"
        ]

        return {
            "success": is_success,
            "pending": is_pending,
            "raw": data
        }

    except Exception as e:
        print("🔥 STATUS CHECK ERROR:", e)
        return {"success": False, "pending": True, "raw": None}