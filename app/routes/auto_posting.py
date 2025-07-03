from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.user import User
from app.routes.profile import get_current_user

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
    return {"message": "Auto-posting campaign stopped"}
