import os
from dotenv import load_dotenv
load_dotenv()

# ==============================
# 🔐 VTPASS CONFIG
# ==============================
# VTPASS_USERNAME = os.getenv("VTPASS_USERNAME", "your_email_here")
# VTPASS_PASSWORD = os.getenv("VTPASS_PASSWORD", "your_api_key_here")
VT_PASS_API_KEY = os.getenv("VT_API_KEY")
VT_PASS_SECRET_KEY = os.getenv("VT_SECRET_KEY")

# ==============================
# 🌐 BASE URL
# ==============================
# VTPASS_BASE_URL = "https://vtpass.com/api"
VTPASS_BASE_URL = "https://sandbox.vtpass.com/api"

# ==============================
# 📡 HEADERS (THIS FIXES YOUR ERROR)
# ==============================
# HEADERS = {
#     "Content-Type": "application/json",
#     "api-key": VTPASS_PASSWORD,
#     "secret-key": VTPASS_USERNAME,
# }
HEADERS = {
    "Content-Type": "application/json",
    "api-key": VT_PASS_API_KEY,
    "secret-key": VT_PASS_SECRET_KEY,
}