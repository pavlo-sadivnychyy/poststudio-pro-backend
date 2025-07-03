from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.user import User
from app.routes.profile import get_current_user
from app.services.auto_posting_service import run_auto_posting
import logging

router = APIRouter()

@router.post("/auto-posting/start")
def start_auto_posting(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    user.auto_posting = True
    db.commit()
    logging.info(f"Auto-posting enabled for user {user.id}")
    return {"message": "Auto-posting campaign started"}

@router.post("/auto-posting/stop")
def stop_auto_posting(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    user.auto_posting = False
    db.commit()
    logging.info(f"Auto-posting disabled for user {user.id}")
    return {"message": "Auto-posting campaign stopped"}

@router.post("/auto-posting/test")
def test_auto_posting(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manual trigger for testing auto-posting immediately"""
    try:
        logging.info(f"Manual auto-posting test triggered by user {current_user.id}")
        run_auto_posting(db)
        return {"message": "Auto-posting test completed - check logs for details"}
    except Exception as e:
        logging.error(f"Error in manual auto-posting test: {str(e)}")
        raise HTTPException(500, f"Auto-posting test failed: {str(e)}")

@router.get("/auto-posting/status")
def get_auto_posting_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current auto-posting status and settings"""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    return {
        "auto_posting_enabled": user.auto_posting,
        "has_access_token": bool(user.access_token),
        "has_schedule_settings": bool(user.schedule_settings),
        "has_content_templates": bool(user.content_templates),
        "schedule_settings": user.schedule_settings,
        "content_templates": user.content_templates
    }