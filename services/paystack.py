import httpx
import os

PAYSTACK_SECRET = os.getenv("PAYSTACK_SECRET_KEY")

async def verify_paystack_transaction(reference: str):
    url = f"https://api.paystack.co/transaction/verify/{reference}"

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET}",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    data = response.json()

    if not data["status"]:
        raise Exception("Paystack verification failed")

    return data["data"]
