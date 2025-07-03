# app/services/user_service.py
import logging
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
            logging.error(f"User {user_id} not found")
            return None
        
        logging.info(f"Found user {user_id}, content_templates: {user.content_templates}")
        
        # Parse JSON strings from database
        content_templates = {}
        
        if user.content_templates:
            try:
                content_templates = json.loads(user.content_templates)
            except (json.JSONDecodeError, TypeError) as e:
                logging.error(f"Failed to parse content_templates for user {user_id}: {e}")
        
        result = {
            "content_templates": content_templates,
        }
        
        logging.info(f"Returning settings for user {user_id}: {result}")
        return result
        
    except Exception as e:
        logging.error(f"Error getting content settings for user {user_id}: {str(e)}")
        return None

def update_content_settings(db: Session, user_id: int, settings_data: dict):
    """Update content settings for a user"""
    try:
        logging.info(f"Updating content settings for user {user_id} with data: {settings_data}")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logging.error(f"User {user_id} not found")
            return None
        
        # Convert dict to JSON strings for database storage
        if 'content_templates' in settings_data:
            user.content_templates = json.dumps(settings_data['content_templates'])
            logging.info(f"Set content_templates to: {user.content_templates}")
        
        # Save to database
        db.commit()
        db.refresh(user)
        
        logging.info(f"Successfully updated content settings for user {user_id}")
        
        # Verify the save
        logging.info(f"Verification - content_templates in DB: {user.content_templates}")
        
        return user
        
    except Exception as e:
        logging.error(f"Error updating content settings for user {user_id}: {str(e)}")
        db.rollback()
        return None

def get_schedule_settings(db: Session, user_id: int):
    """Get schedule settings for a user"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logging.error(f"User {user_id} not found")
            return None
        
        logging.info(f"Found user {user_id}, schedule_settings: {user.schedule_settings}")
        
        # Parse JSON string from database
        if user.schedule_settings:
            try:
                schedule_data = json.loads(user.schedule_settings)
                logging.info(f"Returning schedule settings for user {user_id}: {schedule_data}")
                return schedule_data
            except (json.JSONDecodeError, TypeError) as e:
                logging.error(f"Failed to parse schedule_settings for user {user_id}: {e}")
                return None
        else:
            # Return default settings if none exist
            default_settings = {
                "mode": "daily",
                "timezone": "UTC+2",
                "settings": {
                    "dailyTime": "09:00"
                }
            }
            logging.info(f"No schedule settings found, returning defaults for user {user_id}")
            return default_settings
        
    except Exception as e:
        logging.error(f"Error getting schedule settings for user {user_id}: {str(e)}")
        return None

def update_schedule_settings(db: Session, user_id: int, schedule_data: dict):
    """Update schedule settings for a user"""
    try:
        logging.info(f"Updating schedule settings for user {user_id} with data: {schedule_data}")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logging.error(f"User {user_id} not found")
            return None
        
        # Convert dict to JSON string for database storage
        user.schedule_settings = json.dumps(schedule_data)
        logging.info(f"Set schedule_settings to: {user.schedule_settings}")
        
        # Save to database
        db.commit()
        db.refresh(user)
        
        logging.info(f"Successfully updated schedule settings for user {user_id}")
        
        # Generate summary for response
        summary = generate_schedule_summary(schedule_data)
        
        return {
            "user": user,
            "summary": summary
        }
        
    except Exception as e:
        logging.error(f"Error updating schedule settings for user {user_id}: {str(e)}")
        db.rollback()
        return None

def generate_schedule_summary(schedule_data: dict) -> str:
    """Generate a human-readable summary of the schedule"""
    try:
        mode = schedule_data.get("mode", "unknown")
        timezone = schedule_data.get("timezone", "UTC")
        settings = schedule_data.get("settings", {})
        
        if mode == "daily":
            daily_time = settings.get("dailyTime", "09:00")
            return f"Daily posting enabled at {daily_time} ({timezone})"
        
        elif mode == "manual":
            selected_dates = settings.get("selectedDates", {})
            total_days = len(selected_dates)
            total_posts = sum(len(times) for times in selected_dates.values())
            
            if total_posts == 0:
                return "No posts scheduled"
            
            return f"{total_posts} posts scheduled across {total_days} days ({timezone})"
        
        else:
            return "Schedule configuration saved"
            
    except Exception as e:
        logging.error(f"Error generating schedule summary: {e}")
        return "Schedule settings updated"