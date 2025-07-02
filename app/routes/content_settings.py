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
    settings = get_content_settings(db, current_user.id)
    logging.info(f"Content settings for user {current_user.id}: {settings}")
    if settings is None:
        raise HTTPException(status_code=404, detail="User not found")
    return settings

@router.put("/content-settings")
def update_content_settings_api(
    settings: ContentSettingsRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    updated_user = update_content_settings(db, current_user.id, settings.dict())
    if updated_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Content settings updated successfully"}
