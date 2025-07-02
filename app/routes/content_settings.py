import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.services.user_service import get_content_settings, update_content_settings
from app.routes.profile import get_current_user
from app.schemas.content_settings import ContentSettingsRequest, ContentSettingsResponse

router = APIRouter()

@router.get("/content-settings", response_model=ContentSettingsResponse)
def read_content_settings(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        settings = get_content_settings(db, current_user.id)
        logging.info(f"Content settings for user {current_user.id}: {settings}")
        
        if settings is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Return the dict directly - ContentSettingsResponse will handle it
        return ContentSettingsResponse(
            content_templates=settings.get('content_templates', {}),
            schedule_settings=settings.get('schedule_settings', {
                "timezone": "UTC-5",
                "optimal_times": True,
                "custom_times": []
            })
        )
    except Exception as e:
        logging.error(f"Error fetching content settings for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/content-settings")
def update_content_settings_api(
    settings: ContentSettingsRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        settings_dict = settings.dict()
        logging.info(f"Received settings update for user {current_user.id}: {settings_dict}")
        
        updated_user = update_content_settings(db, current_user.id, settings_dict)
        if updated_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify by reading back the data
        verification = get_content_settings(db, current_user.id)
        logging.info(f"Verification after update: {verification}")
        
        return {"message": "Content settings updated successfully"}
    except Exception as e:
        logging.error(f"Error updating content settings for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update content settings")