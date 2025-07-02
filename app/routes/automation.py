from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.models.database import get_db
from app.services.user_service import update_automation_settings
from app.routes.user import get_current_user  # reuse your existing auth dependency
from app.schemas.automation import AutomationSettingsRequest, AutomationSettingsResponse

router = APIRouter()

@router.get("/automation", response_model=AutomationSettingsResponse)
def get_automation_settings(current_user = Depends(get_current_user)):
    industries = current_user.industries.split(",") if current_user.industries else []
    avoid_topics = current_user.avoid_topics.split(",") if current_user.avoid_topics else []

    return AutomationSettingsResponse(
        auto_posting=current_user.auto_posting,
        auto_commenting=current_user.auto_commenting,
        post_frequency=current_user.post_frequency,
        comment_frequency=current_user.comment_frequency,
        personality_type=current_user.personality_type,
        engagement_style=current_user.engagement_style,
        industries=industries,
        avoid_topics=avoid_topics
    )

@router.put("/automation")
def update_automation(
    settings: AutomationSettingsRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    updated_user = update_automation_settings(db, current_user.id, settings)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Settings updated successfully"}
