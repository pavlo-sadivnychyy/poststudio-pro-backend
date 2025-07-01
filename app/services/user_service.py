from sqlalchemy.orm import Session
from app.models.user import User

def create_or_update_user(
    db: Session, 
    linkedin_id: str, 
    name: str, 
    email: str, 
    access_token: str, 
    linkedin_profile: str = None,
    auto_posting_notifications: bool = True,
    general_notifications: bool = True,
    weekly_email_reports: bool = True
):
    user = db.query(User).filter(User.linkedin_id == linkedin_id).first()
    if user:
        user.access_token = access_token
        user.name = name
        user.email = email
        if linkedin_profile is not None:
            user.linkedin_profile = linkedin_profile
        user.auto_posting_notifications = auto_posting_notifications
        user.general_notifications = general_notifications
        user.weekly_email_reports = weekly_email_reports
    else:
        user = User(
            linkedin_id=linkedin_id,
            name=name,
            email=email,
            access_token=access_token,
            linkedin_profile=linkedin_profile,
            auto_posting_notifications=auto_posting_notifications,
            general_notifications=general_notifications,
            weekly_email_reports=weekly_email_reports
        )
        db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()
