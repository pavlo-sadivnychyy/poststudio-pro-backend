from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.subscription import Subscription
from app.models.user import User
from datetime import datetime
import hashlib
import base64
import uuid
import os

router = APIRouter()

MERCHANT_ACCOUNT = os.getenv("WFP_MERCHANT_ACCOUNT", "demo")
MERCHANT_SECRET_KEY = os.getenv("WFP_SECRET_KEY", "secret")
DOMAIN_NAME = os.getenv("APP_DOMAIN", "http://localhost:8000")
SERVICE_URL = f"{DOMAIN_NAME}/billing/callback"

class PayRequest(BaseModel):
    user_id: int
    plan: str  # "basic" or "pro"
    amount: float
    email: str

def generate_signature(data: dict, secret: str):
    keys = [
        data["merchantAccount"],
        data["merchantDomainName"],
        data["orderReference"],
        str(data["orderDate"]),
        str(data["amount"]),
        data["currency"],
        ",".join(data["productName"]),
        ",".join(map(str, data["productCount"])),
        ",".join(map(str, data["productPrice"]))
    ]
    signature_str = ";".join(keys)
    return base64.b64encode(hashlib.sha1((signature_str + secret).encode()).digest()).decode()

@router.post("/pay")
def create_payment(data: PayRequest):
    order_ref = str(uuid.uuid4())
    order_date = int(datetime.utcnow().timestamp())
    payload = {
        "merchantAccount": MERCHANT_ACCOUNT,
        "merchantDomainName": "poststudio.pro",
        "orderReference": order_ref,
        "orderDate": order_date,
        "amount": data.amount,
        "currency": "USD",
        "productName": [f"PostStudio {data.plan.capitalize()} Plan"],
        "productPrice": [data.amount],
        "productCount": [1],
        "clientEmail": data.email,
        "orderTimeout": 86400,
        "serviceUrl": SERVICE_URL,
    }
    payload["merchantSignature"] = generate_signature(payload, MERCHANT_SECRET_KEY)
    return {
        "url": "https://secure.wayforpay.com/pay",
        "params": payload
    }

@router.post("/callback")
def handle_callback(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    email = data.get("email")
    status = data.get("transactionStatus")

    if status == "Approved":
        user = db.query(User).filter(User.email == email).first()
        if user:
            subscription = Subscription(user_id=user.id, plan="pro", status="active")
            db.add(subscription)
            db.commit()
            return {"status": "success"}
    return {"status": "ignored"}