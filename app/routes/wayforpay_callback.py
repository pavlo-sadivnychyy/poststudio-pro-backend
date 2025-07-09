# app/routes/wayforpay_callback.py
import os, hmac, hashlib
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.user import User
from datetime import datetime
from dateutil.relativedelta import relativedelta

router = APIRouter()

@router.post("/callback")
async def wayforpay_callback(request: Request, db: Session = Depends(get_db)):
    data = await request.json()

    # verify signature
    sig_fields = [
      data["merchantAccount"],
      data["merchantDomainName"],
      data["orderReference"],
      data["orderDate"],
      data["amount"],
      data["currency"],
      data["authCode"],
      data["cardPan"],
      data["transactionStatus"]
    ]
    sig_str = ";".join(map(str, sig_fields))
    expected = hmac.new(
        os.getenv("WAYFORPAY_SECRET_KEY").encode(),
        sig_str.encode(),
        hashlib.sha256
    ).hexdigest()
    if expected != data.get("merchantSignature"):
        raise HTTPException(400, "Invalid signature")

    # only accept on Approved
    if data["transactionStatus"] == "Approved":
        # parse userId from orderReference: "sub_{userId}_{ts}"
        try:
            _, uid, _ = data["orderReference"].split("_", 2)
            user = db.query(User).get(int(uid))
        except:
            user = None

        if user:
            user.subscription_active = True
            user.subscription_plan   = data["productName"][0]
            # extend expiration one month from now
            user.subscription_expires = datetime.utcnow() + relativedelta(months=+1)
            db.commit()

    return {"orderReference": data["orderReference"], "status": "accept"}
