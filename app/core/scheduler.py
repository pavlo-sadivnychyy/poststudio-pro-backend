import logging
import asyncio
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from sqlalchemy.orm import Session
from app.models.database import SessionLocal
from app.services.auto_posting_service import run_auto_posting
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

def start_scheduler(app: FastAPI):
    """Initialize the scheduler but don't add any jobs yet"""
    
    async def check_and_post():
        """Check all users and post if it's their scheduled time"""
        db: Session = SessionLocal()
        try:
            logger.info("🔄 Checking scheduled posts...")
            
            from app.models.user import User
            
            # Only get users who have auto_posting enabled
            active_users = db.query(User).filter(User.auto_posting == True).all()
            
            if not active_users:
                logger.info("📝 No users with active auto-posting found")
                return
            
            logger.info(f"👥 Found {len(active_users)} users with auto-posting enabled")
            
            # Check each user's schedule
            for user in active_users:
                try:
                    if should_user_post_now(user):
                        logger.info(f"⏰ Time to post for user {user.id}")
                        await asyncio.get_event_loop().run_in_executor(None, post_for_user, db, user)
                    else:
                        logger.debug(f"⏸️ Not time to post for user {user.id}")
                except Exception as e:
                    logger.error(f"❌ Error checking user {user.id}: {str(e)}")
            
        except Exception as e:
            logger.error(f"❌ Error in scheduled check: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            db.close()

    # Run every minute to check for scheduled posts
    scheduler.add_job(
        check_and_post,
        CronTrigger(minute="*"),  # Every minute
        id="check_scheduled_posts",
        replace_existing=True,
        max_instances=1
    )
    
    scheduler.start()
    logger.info("🚀 Scheduler started - checking for scheduled posts every minute")

def should_user_post_now(user) -> bool:
    """Check if this specific user should post right now"""
    try:
        if not user.schedule_settings:
            logger.debug(f"User {user.id} has no schedule settings")
            return False
            
        schedule = json.loads(user.schedule_settings)
        current_time = datetime.now(timezone.utc)
        
        if schedule.get('mode') == 'daily':
            daily_time = schedule.get('settings', {}).get('dailyTime', '09:00')
            current_hour_minute = current_time.strftime('%H:%M')
            
            # Check if current time matches daily time (within 1 minute)
            scheduled_hour, scheduled_minute = daily_time.split(':')
            current_hour = current_time.hour
            current_minute = current_time.minute
            
            if (int(scheduled_hour) == current_hour and 
                int(scheduled_minute) == current_minute):
                logger.info(f"✅ Daily post time match for user {user.id}: {daily_time}")
                return True
                
        elif schedule.get('mode') == 'manual':
            selected_dates = schedule.get('settings', {}).get('selectedDates', {})
            current_date = current_time.strftime('%Y-%m-%d')
            current_hour_minute = current_time.strftime('%H:%M')
            
            if current_date in selected_dates:
                scheduled_times = selected_dates[current_date]
                
                for scheduled_time in scheduled_times:
                    if scheduled_time == current_hour_minute:
                        logger.info(f"✅ Manual post time match for user {user.id}: {current_date} {scheduled_time}")
                        return True
            
    except Exception as e:
        logger.error(f"Error checking schedule for user {user.id}: {str(e)}")
        return False
    
    return False

def post_for_user(db: Session, user):
    """Post content for a specific user"""
    try:
        from app.services.auto_posting_service import (
            get_content_template_settings, 
            get_valid_tone, 
            generate_linkedin_post
        )
        from app.services.linkedin_service import post_linkedin_content
        from app.schemas.post_generator import PostGenerateRequest
        
        logger.info(f"🎯 Generating post for user {user.id}")
        
        # Check if user has valid access token
        if not user.access_token:
            logger.warning(f"User {user.id} has no access token")
            return False
        
        # Get content template settings
        content_templates = get_content_template_settings(user)
        if not content_templates:
            logger.warning(f"User {user.id} has no content templates")
            return False
        
        # Pick the first available template (you can make this smarter)
        template_name = next(iter(content_templates.keys()), "story")
        template = content_templates[template_name]
        
        # Create post request from template with valid tone
        raw_tone = template.get("tone", user.personality_type or "professional")
        valid_tone = get_valid_tone(raw_tone)
        
        post_request = PostGenerateRequest(
            topic=template.get("topic", "Professional Growth"),
            industry=template.get("industry", user.industry or "General"),
            tone=valid_tone,
            post_type=template.get("post_type", "story"),
            post_length=template.get("post_length", 150),
            include_hashtags=template.get("include_hashtags", True),
            include_emojis=template.get("include_emojis", True)
        )
        
        # Generate the content
        content = generate_linkedin_post(post_request)
        if not content:
            logger.warning(f"Failed to generate post content for user {user.id}")
            return False
        
        logger.info(f"📝 Generated content for user {user.id}: {content[:100]}...")
        
        # Post to LinkedIn
        success = post_linkedin_content(user.access_token, content)
        if success:
            logger.info(f"✅ Successfully posted to LinkedIn for user {user.id}")
            
            # Mark this time slot as used (optional - to prevent duplicate posts)
            # You could add logic here to remove this time slot or mark it as used
            
            return True
        else:
            logger.error(f"❌ Failed to post to LinkedIn for user {user.id}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error posting for user {user.id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def shutdown_scheduler():
    """Shutdown the scheduler gracefully"""
    try:
        scheduler.shutdown(wait=True)
        logger.info("🛑 Scheduler stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")

def get_scheduler_status():
    """Get current scheduler status"""
    return {
        "running": scheduler.running,
        "jobs": [
            {
                "id": job.id,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            }
            for job in scheduler.get_jobs()
        ]
    }