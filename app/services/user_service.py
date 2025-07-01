# app/services/user_service.py
from sqlalchemy.orm import Session
from app.models.user import User

def create_or_update_user(
    db: Session, 
    linkedin_id: str, 
    name: str, 
    email: str, 
    access_token: str, 
    linkedin_profile: str = None,
    company: str = None,
    industry: str = None,
    auto_posting_notifications: bool = True,
    general_notifications: bool = True,
    weekly_email_reports: bool = True
):
    try:
        print(f"Looking for user with LinkedIn ID: {linkedin_id}")
        user = db.query(User).filter(User.linkedin_id == linkedin_id).first()
        
        if user:
            print(f"Updating existing user: {user.id}")
            # Update existing user
            user.access_token = access_token
            user.name = name
            user.email = email
            if linkedin_profile is not None:
                user.linkedin_profile = linkedin_profile
            if company is not None:
                user.company = company
            if industry is not None:
                user.industry = industry
            user.auto_posting_notifications = auto_posting_notifications
            user.general_notifications = general_notifications
            user.weekly_email_reports = weekly_email_reports
        else:
            print(f"Creating new user with LinkedIn ID: {linkedin_id}")
            # Create new user
            user = User(
                linkedin_id=linkedin_id,
                name=name,
                email=email,
                access_token=access_token,
                linkedin_profile=linkedin_profile,
                company=company,
                industry=industry,
                auto_posting_notifications=auto_posting_notifications,
                general_notifications=general_notifications,
                weekly_email_reports=weekly_email_reports
            )
            db.add(user)
        
        # Commit and refresh
        db.commit()
        db.refresh(user)
        
        print(f"User successfully created/updated: ID={user.id}, Email={user.email}")
        return user
        
    except Exception as e:
        print(f"Error in create_or_update_user: {e}")
        db.rollback()
        raise e
        
def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def update_user_profile(
    db: Session,
    user_id: int,
    name: str = None,
    email: str = None,
    company: str = None,
    industry: str = None,
    linkedin_profile: str = None,
    auto_posting_notifications: bool = None,
    general_notifications: bool = None,
    weekly_email_reports: bool = None
):
    """Update user profile with validation"""
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    
    # Update only provided fields
    if name is not None:
        user.name = name
    if email is not None:
        user.email = email
    if company is not None:
        user.company = company
    if industry is not None:
        user.industry = industry
    if linkedin_profile is not None:
        user.linkedin_profile = linkedin_profile
    if auto_posting_notifications is not None:
        user.auto_posting_notifications = auto_posting_notifications
    if general_notifications is not None:
        user.general_notifications = general_notifications
    if weekly_email_reports is not None:
        user.weekly_email_reports = weekly_email_reports
    
    try:
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        raise e