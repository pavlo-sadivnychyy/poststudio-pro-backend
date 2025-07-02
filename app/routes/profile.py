# app/routers/user.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, EmailStr
from app.models.database import get_db
from app.services.user_service import get_user_by_id, update_user_profile
import jwt
import os
import traceback

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
    email: EmailStr | None = None  # Use EmailStr for validation
    company: str | None = None
    industry: str | None = None
    linkedin_profile: str | None = None
    auto_posting_notifications: bool | None = None
    general_notifications: bool | None = None
    weekly_email_reports: bool | None = None

@router.get("/profile")
def get_profile(current_user = Depends(get_current_user)):
    """Get current user profile"""
    return {
        "id": current_user.id,
        "linkedin_id": current_user.linkedin_id,
        "email": current_user.email,
        "name": current_user.name,
        "access_token": current_user.access_token,
        "linkedin_profile": current_user.linkedin_profile,
        "company": current_user.company,
        "industry": current_user.industry,

        "auto_posting_notifications": current_user.auto_posting_notifications,
        "general_notifications": current_user.general_notifications,
        "weekly_email_reports": current_user.weekly_email_reports,

        "auto_posting": current_user.auto_posting,
        "auto_commenting": current_user.auto_commenting,
        "post_frequency": current_user.post_frequency,
        "comment_frequency": current_user.comment_frequency,
        "personality_type": current_user.personality_type,
        "engagement_style": current_user.engagement_style,
        "industries": current_user.industries,
        "avoid_topics": current_user.avoid_topics,

        "content_templates": current_user.content_templates,
        "schedule_settings": current_user.schedule_settings,

        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
    }

@router.put("/profile")
def update_profile(
    update: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update current user profile"""
    try:
        # Use the service function for better error handling
        updated_user = update_user_profile(
            db=db,
            user_id=current_user.id,
            name=update.name,
            email=update.email,
            company=update.company,
            industry=update.industry,
            linkedin_profile=update.linkedin_profile,
            auto_posting_notifications=update.auto_posting_notifications,
            general_notifications=update.general_notifications,
            weekly_email_reports=update.weekly_email_reports
        )
        
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "message": "Profile updated successfully",
            "user": {
                "id": updated_user.id,
                "name": updated_user.name,
                "email": updated_user.email,
                "company": updated_user.company,
                "industry": updated_user.industry,
                "linkedin_profile": updated_user.linkedin_profile,
                "auto_posting_notifications": updated_user.auto_posting_notifications,
                "general_notifications": updated_user.general_notifications,
                "weekly_email_reports": updated_user.weekly_email_reports,
            }
        }
        
    except IntegrityError as e:
        db.rollback()
        if "email" in str(e):
            raise HTTPException(status_code=400, detail="Email already exists")
        raise HTTPException(status_code=400, detail="Database constraint violation")
    
    except Exception as e:
        print(f"Error updating profile: {str(e)}")
        print(traceback.format_exc())  # Log full traceback
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Debug endpoint to check user model fields
@router.get("/debug/user-fields")
def debug_user_fields(current_user = Depends(get_current_user)):
    """Debug endpoint to see what fields exist on user model"""
    user_dict = {}
    for column in current_user.__table__.columns:
        user_dict[column.name] = getattr(current_user, column.name, "N/A")
    return {
        "user_id": current_user.id,
        "available_fields": user_dict,
        "table_name": current_user.__tablename__
    }

@router.get("/debug/users")
def debug_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return {"count": len(users), "users": [{"id": u.id, "email": u.email} for u in users]}