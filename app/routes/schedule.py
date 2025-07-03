# app/routes/schedule.py
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.services.user_service import get_schedule_settings, update_schedule_settings
from app.routes.profile import get_current_user  # Adjust import path as needed
from app.schemas.schedule import (
    ScheduleSettingsRequest, 
    ScheduleSettingsResponse, 
    ScheduleUpdateResponse
)

router = APIRouter()

@router.get("/schedule-settings", response_model=ScheduleSettingsResponse)
def get_user_schedule_settings(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get the current user's schedule settings"""
    try:
        schedule_data = get_schedule_settings(db, current_user.id)
        logging.info(f"Schedule settings for user {current_user.id}: {schedule_data}")
        
        if schedule_data is None:
            # Return default settings if user not found or no settings
            default_settings = {
                "mode": "daily",
                "timezone": "UTC+2", 
                "settings": {"dailyTime": "09:00"}
            }
            return ScheduleSettingsResponse(**default_settings)
        
        return ScheduleSettingsResponse(**schedule_data)
        
    except Exception as e:
        logging.error(f"Error fetching schedule settings for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/schedule-settings", response_model=ScheduleUpdateResponse)
def update_user_schedule_settings(
    schedule_request: ScheduleSettingsRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Update the current user's schedule settings"""
    try:
        # Convert Pydantic model to dict for storage
        schedule_data = {
            "mode": schedule_request.mode,
            "timezone": schedule_request.timezone,
            "settings": schedule_request.settings.dict() if hasattr(schedule_request.settings, 'dict') else schedule_request.settings
        }
        
        logging.info(f"Received schedule update for user {current_user.id}: {schedule_data}")
        
        # Update in database
        result = update_schedule_settings(db, current_user.id, schedule_data)
        
        if result is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        logging.info(f"Successfully updated schedule for user {current_user.id}")
        
        return ScheduleUpdateResponse(
            message="Schedule settings updated successfully",
            schedule_summary=result["summary"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating schedule settings for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update schedule settings")

@router.delete("/schedule-settings")
def clear_user_schedule_settings(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Clear/reset the current user's schedule settings"""
    try:
        # Reset to default daily schedule
        default_settings = {
            "mode": "daily",
            "timezone": "UTC+2",
            "settings": {"dailyTime": "09:00"}
        }
        
        result = update_schedule_settings(db, current_user.id, default_settings)
        
        if result is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "message": "Schedule settings reset to default",
            "schedule_summary": "Daily posting enabled at 09:00 (UTC+2)"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error clearing schedule settings for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear schedule settings")

@router.get("/schedule-summary")
def get_schedule_summary(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get a quick summary of the user's current schedule"""
    try:
        schedule_data = get_schedule_settings(db, current_user.id)
        
        if schedule_data is None:
            return {"summary": "No schedule configured"}
        
        from app.services.user_service import generate_schedule_summary
        summary = generate_schedule_summary(schedule_data)
        
        return {
            "summary": summary,
            "mode": schedule_data.get("mode", "unknown"),
            "timezone": schedule_data.get("timezone", "UTC")
        }
        
    except Exception as e:
        logging.error(f"Error getting schedule summary for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")