# app/services/user_service.py
from sqlalchemy.orm import Session
from app.models.user import User
import json

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

def update_automation_settings(db: Session, user_id: int, settings):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    
    data = settings.dict() if hasattr(settings, "dict") else settings

    for key, value in data.items():
        if value is None:
            continue
        if isinstance(value, list):
            value = ",".join(value)
        setattr(user, key, value)

    try:
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        print(f"Error updating automation settings: {e}")
        raise e

def safe_load_json(s):
    if not s:
        return {}
    try:
        return json.loads(s)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return {}

def get_content_settings(db: Session, user_id: int):
    """Get content settings for a user"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # If your User model has content_settings fields directly
        if hasattr(user, 'content_templates') and hasattr(user, 'schedule_settings'):
            return {
                "content_templates": user.content_templates or {},
                "schedule_settings": user.schedule_settings or {
                    "timezone": "UTC-5",
                    "optimal_times": True,
                    "custom_times": ["09:00", "14:00", "17:00"]
                }
            }
        
        # If you store settings as JSON in a single field
        elif hasattr(user, 'content_settings'):
            if user.content_settings:
                try:
                    settings = json.loads(user.content_settings) if isinstance(user.content_settings, str) else user.content_settings
                    return settings
                except (json.JSONDecodeError, TypeError):
                    logging.error(f"Failed to parse content_settings for user {user_id}")
                    return None
            else:
                return None
        
        # If no settings found, return None
        return None
        
    except Exception as e:
        logging.error(f"Error getting content settings for user {user_id}: {str(e)}")
        return None

def update_content_settings(db: Session, user_id: int, settings_data: dict):
    """Update content settings for a user"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # If your User model has separate fields for content_templates and schedule_settings
        if hasattr(user, 'content_templates') and hasattr(user, 'schedule_settings'):
            if 'content_templates' in settings_data:
                user.content_templates = settings_data['content_templates']
            if 'schedule_settings' in settings_data:
                user.schedule_settings = settings_data['schedule_settings']
        
        # If you store settings as JSON in a single field
        elif hasattr(user, 'content_settings'):
            user.content_settings = json.dumps(settings_data) if not isinstance(settings_data, str) else settings_data
        
        else:
            # If the fields don't exist, you might need to add them to your User model
            logging.error(f"User model doesn't have content settings fields")
            return None
        
        # CRITICAL: This is probably what's missing - you need to commit the changes!
        db.commit()   # Save changes to database
        db.refresh(user)  # Refresh the user object with latest data
        
        logging.info(f"Successfully updated content settings for user {user_id}")
        return user
        
    except Exception as e:
        logging.error(f"Error updating content settings for user {user_id}: {str(e)}")
        db.rollback()  # Rollback in case of error
        return None
