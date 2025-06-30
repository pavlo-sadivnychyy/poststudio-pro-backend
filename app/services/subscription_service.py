from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.subscription import Subscription

def require_subscription(user_id: int, db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.user_id == user_id, Subscription.status == "active").first()
    if not sub:
        raise HTTPException(status_code=403, detail="Active subscription required")
    return True