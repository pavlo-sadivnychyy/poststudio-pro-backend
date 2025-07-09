# app/routes/payments.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import os, time, hmac, hashlib

from sqlalchemy.orm import Session
from app.models.database import get_db
from app.routes.profile import get_current_user
from app.models.user import User

router = APIRouter()

MERCHANT = os.getenv("WAYFORPAY_MERCHANT_ACCOUNT")
SECRET   = os.getenv("WAYFORPAY_SECRET_KEY")
BASE_URL = os.getenv("APP_BASE_URL")  # e.g. https://your-domain.com

class SubscribeRequest(BaseModel):
    plan_id: str
    amount: float

@router.post("/subscribe")
def create_subscription(
    req: SubscribeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Build a WayForPay payload that will set up a recurring monthly charge."""
    order_ref  = f"sub_{current_user.id}_{int(time.time())}"
    order_date = int(time.time())

    payload = {
      "merchantAccount":      MERCHANT,
      "merchantDomainName":   BASE_URL.replace("https://",""),
      "orderReference":       order_ref,
      "orderDate":            order_date,
      "amount":               req.amount,
      "currency":             "USD",
      "productName":          [req.plan_id],
      "productPrice":         [req.amount],
      "productCount":         [1],
      "serviceUrl":           f"{BASE_URL}/payments/callback",
      "returnUrl":            f"{BASE_URL}/payment-success",
      "clientFirstName":      current_user.name.split()[0],
      "clientLastName":       current_user.name.split()[-1],
      "clientEmail":          current_user.email,
      # ← this block enables recurring monthly charges
      "recurringData": {
        "recurrence":       "MONTH",
        "period":           1,
        "recurrenceTimes":  0,          # 0 = infinite until canceled
        "startDate":        order_date
      }
    }

    # build signature
    sign_fields = [
      payload["merchantAccount"],
      payload["merchantDomainName"],
      payload["orderReference"],
      str(payload["orderDate"]),
      str(payload["amount"]),
      payload["currency"],
      *payload["productName"],
      *[str(x) for x in payload["productCount"]],
      *[str(x) for x in payload["productPrice"]],
      payload["recurringData"]["recurrence"],
      str(payload["recurringData"]["period"]),
      str(payload["recurringData"]["recurrenceTimes"]),
      str(payload["recurringData"]["startDate"])
    ]
    sig_str = ";".join(sign_fields)
    signature = hmac.new(SECRET.encode(), sig_str.encode(), hashlib.sha256).hexdigest()
    payload["merchantSignature"] = signature

    # return the form payload to your frontend
    return {"wayforpay": payload}
