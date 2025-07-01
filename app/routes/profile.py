from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models.database import get_db
from app.services.user_service import get_user_by_id
import jwt
import os

router = APIRouter()
security = HTTPBearer()

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "supersecretjwtkey")

def get_current_user(token: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token.credentials, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        user = get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

class UserUpdateRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    company: str | None = None
    industry: str | None = None
    linkedin_profile: str | None = None
    auto_posting_notifications: bool | None = None
    general_notifications: bool | None = None
    weekly_email_reports: bool | None = None

@router.get("/profile")
def get_profile(current_user = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "company": getattr(current_user, "company", None),
        "industry": getattr(current_user, "industry", None),
        "linkedin_profile": getattr(current_user, "linkedin_profile", None),
        "auto_posting_notifications": getattr(current_user, "auto_posting_notifications", None),
        "general_notifications": getattr(current_user, "general_notifications", None),
        "weekly_email_reports": getattr(current_user, "weekly_email_reports", None),
    }

@router.put("/profile")
def update_profile(
    update: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    user = get_user_by_id(db, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Оновлюємо поля, якщо передані
    if update.name is not None:
        user.name = update.name
    if update.email is not None:
        user.email = update.email
    if update.company is not None:
        user.company = update.company
    if update.industry is not None:
        user.industry = update.industry
    if update.linkedin_profile is not None:
        user.linkedin_profile = update.linkedin_profile
    if update.auto_posting_notifications is not None:
        user.auto_posting_notifications = update.auto_posting_notifications
    if update.general_notifications is not None:
        user.general_notifications = update.general_notifications
    if update.weekly_email_reports is not None:
        user.weekly_email_reports = update.weekly_email_reports

    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "company": user.company,
        "industry": user.industry,
        "linkedin_profile": user.linkedin_profile,
        "auto_posting_notifications": user.auto_posting_notifications,
        "general_notifications": user.general_notifications,
        "weekly_email_reports": user.weekly_email_reports,
    }
