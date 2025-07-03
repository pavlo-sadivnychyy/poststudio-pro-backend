import json
import logging
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
        from app.services.auto_posting_service import run_auto_posting
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

@router.post("/auto-posting/debug")
def debug_auto_posting(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Debug endpoint to check all auto-posting components"""
    debug_info = {
        "user_id": current_user.id,
        "auto_posting_enabled": current_user.auto_posting,
        "has_access_token": bool(current_user.access_token),
        "access_token_preview": current_user.access_token[:20] + "..." if current_user.access_token else None,
        "has_schedule_settings": bool(current_user.schedule_settings),
        "has_content_templates": bool(current_user.content_templates),
        "schedule_settings": current_user.schedule_settings,
        "content_templates": current_user.content_templates,
        "checks": {}
    }
    
    # Check 1: User settings
    if not current_user.auto_posting:
        debug_info["checks"]["auto_posting"] = "❌ Auto-posting is disabled"
    else:
        debug_info["checks"]["auto_posting"] = "✅ Auto-posting is enabled"
    
    # Check 2: Access token
    if not current_user.access_token:
        debug_info["checks"]["access_token"] = "❌ No LinkedIn access token"
    else:
        debug_info["checks"]["access_token"] = "✅ LinkedIn access token exists"
    
    # Check 3: Schedule settings
    try:
        if current_user.schedule_settings:
            schedule = json.loads(current_user.schedule_settings)
            debug_info["checks"]["schedule"] = f"✅ Schedule mode: {schedule.get('mode', 'unknown')}"
            
            # Check if should post now
            try:
                from app.services.auto_posting_service import should_post_now
                should_post = should_post_now(current_user)
                debug_info["checks"]["should_post_now"] = f"{'✅' if should_post else '❌'} Should post now: {should_post}"
            except Exception as e:
                debug_info["checks"]["should_post_now"] = f"❌ Schedule check error: {str(e)}"
        else:
            debug_info["checks"]["schedule"] = "❌ No schedule settings"
    except Exception as e:
        debug_info["checks"]["schedule"] = f"❌ Schedule error: {str(e)}"
    
    # Check 4: Content templates
    try:
        if current_user.content_templates:
            templates = json.loads(current_user.content_templates)
            debug_info["checks"]["templates"] = f"✅ {len(templates)} content templates"
        else:
            debug_info["checks"]["templates"] = "❌ No content templates"
    except Exception as e:
        debug_info["checks"]["templates"] = f"❌ Template error: {str(e)}"
    
    return debug_info

@router.post("/auto-posting/force-test")
def force_test_posting(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Force test a LinkedIn post regardless of schedule"""
    try:
        from app.services.auto_posting_service import generate_linkedin_post
        from app.services.linkedin_service import post_linkedin_content
        from app.schemas.post_generator import PostGenerateRequest
        
        # Check prerequisites
        if not current_user.access_token:
            return {"error": "No LinkedIn access token found"}
        
        # Generate test content - fix tone validation
        valid_tone = "Professional"  # Default to valid tone
        if current_user.personality_type:
            tone_mapping = {
                "professional": "Professional",
                "casual": "Casual & Friendly", 
                "friendly": "Casual & Friendly",
                "thought_leader": "Thought Leader",
                "storytelling": "Storytelling",
                "motivational": "Motivational"
            }
            valid_tone = tone_mapping.get(current_user.personality_type.lower(), "Professional")
        
        test_request = PostGenerateRequest(
            topic="Test Post from AI Automation",
            industry=current_user.industry or "Technology",
            tone=valid_tone,
            post_type="story",
            post_length=100,
            include_hashtags=True,
            include_emojis=True
        )
        
        logging.info(f"Generating test post for user {current_user.id}")
        content = generate_linkedin_post(test_request)
        
        if not content:
            return {"error": "Failed to generate content"}
        
        logging.info(f"Generated content: {content}")
        
        # Try to post to LinkedIn
        success = post_linkedin_content(current_user.access_token, content)
        
        return {
            "success": success,
            "content": content,
            "message": "Post created successfully!" if success else "Failed to post to LinkedIn"
        }
        
    except Exception as e:
        logging.error(f"Force test error: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {"error": str(e)}

@router.post("/auto-posting/add-test-schedule")
def add_test_schedule(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add today's date to schedule for testing"""
    try:
        from datetime import datetime, timedelta
        
        # Get current time + 5 minutes for testing
        now = datetime.now()
        test_time = now + timedelta(minutes=5)
        today_str = now.strftime('%Y-%m-%d')
        test_time_str = test_time.strftime('%H:%M')
        
        # Get current schedule or create new one
        if current_user.schedule_settings:
            schedule = json.loads(current_user.schedule_settings)
        else:
            schedule = {"mode": "manual", "timezone": "UTC+2", "settings": {"selectedDates": {}}}
        
        # Add today's date with test time
        if "selectedDates" not in schedule.get("settings", {}):
            schedule["settings"]["selectedDates"] = {}
        
        schedule["settings"]["selectedDates"][today_str] = [test_time_str]
        
        # Update user
        current_user.schedule_settings = json.dumps(schedule)
        db.commit()
        
        return {
            "message": f"Added test schedule for today ({today_str}) at {test_time_str}",
            "schedule": schedule,
            "note": "The scheduler will check this in the next 15 minutes"
        }
        
    except Exception as e:
        logging.error(f"Error adding test schedule: {str(e)}")
        raise HTTPException(500, f"Failed to add test schedule: {str(e)}")

@router.get("/auto-posting/timezone-debug")
def debug_timezone_calculation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Debug timezone calculations to see why posting isn't happening"""
    try:
        from datetime import datetime, timezone as dt_timezone, timedelta
        
        if not current_user.schedule_settings:
            return {"error": "No schedule settings found"}
        
        schedule = json.loads(current_user.schedule_settings)
        current_utc = datetime.now(dt_timezone.utc)
        
        # Parse user timezone
        user_timezone = schedule.get('timezone', 'UTC+0')
        
        def parse_timezone_offset(timezone_str):
            if timezone_str == 'UTC+0' or timezone_str == 'UTC':
                return timedelta(0)
            if timezone_str.startswith('UTC+'):
                hours = int(timezone_str[4:])
                return timedelta(hours=hours)
            elif timezone_str.startswith('UTC-'):
                hours = int(timezone_str[4:])
                return timedelta(hours=-hours)
            else:
                return timedelta(0)
        
        timezone_offset = parse_timezone_offset(user_timezone)
        user_local_time = current_utc + timezone_offset
        
        debug_info = {
            "current_utc_time": current_utc.strftime('%Y-%m-%d %H:%M:%S UTC'),
            "user_timezone": user_timezone,
            "timezone_offset_hours": timezone_offset.total_seconds() / 3600,
            "user_local_time": user_local_time.strftime('%Y-%m-%d %H:%M:%S'),
            "user_local_date": user_local_time.strftime('%Y-%m-%d'),
            "user_local_time_only": user_local_time.strftime('%H:%M'),
            "schedule_mode": schedule.get('mode'),
            "schedule_check": {}
        }
        
        if schedule.get('mode') == 'manual':
            selected_dates = schedule.get('settings', {}).get('selectedDates', {})
            current_date = user_local_time.strftime('%Y-%m-%d')
            current_time_str = user_local_time.strftime('%H:%M')
            
            debug_info["schedule_check"] = {
                "selected_dates": selected_dates,
                "today_in_schedule": current_date in selected_dates,
                "today_scheduled_times": selected_dates.get(current_date, []),
                "current_time_matches": current_time_str in selected_dates.get(current_date, []),
                "should_post_now": current_time_str in selected_dates.get(current_date, [])
            }
        
        return debug_info
        
    except Exception as e:
        logging.error(f"Error in timezone debug: {str(e)}")
        return {"error": str(e)}

@router.post("/auto-posting/force-schedule-check")
def force_schedule_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Force check if user should post now (for testing)"""
    try:
        from app.core.scheduler import should_user_post_now
        
        should_post = should_user_post_now(current_user)
        
        return {
            "user_id": current_user.id,
            "auto_posting_enabled": current_user.auto_posting,
            "should_post_now": should_post,
            "message": "Check complete - see server logs for detailed timing info"
        }
        
    except Exception as e:
        logging.error(f"Error in force schedule check: {str(e)}")
        return {"error": str(e)}

@router.get("/auto-posting/scheduler-status")
def get_scheduler_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current scheduler status"""
    try:
        from app.core.scheduler import get_scheduler_status
        from datetime import datetime
        
        status = get_scheduler_status()
        
        # Add user-specific info
        status["user_auto_posting_enabled"] = current_user.auto_posting
        status["total_active_users"] = db.query(User).filter(User.auto_posting == True).count()
        status["current_time"] = datetime.now().isoformat()
        
        return status
        
    except Exception as e:
        logging.error(f"Error getting scheduler status: {str(e)}")
        return {"error": str(e)}

@router.get("/auto-posting/schedule-debug")
def debug_schedule_timing(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Debug schedule timing to see why posts aren't being scheduled"""
    try:
        from datetime import datetime, timezone as dt_timezone
        from app.services.auto_posting_service import should_post_now
        
        if not current_user.schedule_settings:
            return {"error": "No schedule settings found"}
        
        schedule = json.loads(current_user.schedule_settings)
        current_time = datetime.now(dt_timezone.utc)
        
        debug_info = {
            "current_time_utc": current_time.isoformat(),
            "current_time_local": current_time.strftime('%Y-%m-%d %H:%M'),
            "schedule_mode": schedule.get('mode'),
            "schedule_timezone": schedule.get('timezone'),
            "should_post_now": should_post_now(current_user),
            "schedule_analysis": {}
        }
        
        if schedule.get('mode') == 'manual':
            selected_dates = schedule.get('settings', {}).get('selectedDates', {})
            current_date = current_time.strftime('%Y-%m-%d')
            
            debug_info["schedule_analysis"] = {
                "current_date": current_date,
                "scheduled_dates": list(selected_dates.keys()),
                "has_today": current_date in selected_dates,
                "today_times": selected_dates.get(current_date, []),
                "all_scheduled_times": selected_dates
            }
            
            if current_date in selected_dates:
                current_time_str = current_time.strftime('%H:%M')
                for scheduled_time in selected_dates[current_date]:
                    scheduled_hour, scheduled_minute = scheduled_time.split(':')
                    scheduled_total_minutes = int(scheduled_hour) * 60 + int(scheduled_minute)
                    current_total_minutes = current_time.hour * 60 + current_time.minute
                    time_diff = abs(current_total_minutes - scheduled_total_minutes)
                    
                    debug_info["schedule_analysis"][f"time_check_{scheduled_time}"] = {
                        "scheduled_time": scheduled_time,
                        "current_time": current_time_str,
                        "time_difference_minutes": time_diff,
                        "within_15_min_window": time_diff <= 15
                    }
        
        elif schedule.get('mode') == 'daily':
            daily_time = schedule.get('settings', {}).get('dailyTime', '09:00')
            current_hour_minute = current_time.strftime('%H:%M')
            
            scheduled_hour, scheduled_minute = daily_time.split(':')
            scheduled_total_minutes = int(scheduled_hour) * 60 + int(scheduled_minute)
            current_total_minutes = current_time.hour * 60 + current_time.minute
            time_diff = abs(current_total_minutes - scheduled_total_minutes)
            
            debug_info["schedule_analysis"] = {
                "daily_time": daily_time,
                "current_time": current_hour_minute,
                "time_difference_minutes": time_diff,
                "within_15_min_window": time_diff <= 15
            }
        
        return debug_info
        
    except Exception as e:
        logging.error(f"Error debugging schedule: {str(e)}")
        return {"error": str(e)}

@router.get("/auto-posting/linkedin-debug")
def comprehensive_linkedin_debug(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Comprehensive LinkedIn API debugging"""
    try:
        from app.services.linkedin_service import (
            get_linkedin_profile_info, 
            check_linkedin_permissions,
            try_simple_text_post
        )
        
        if not current_user.access_token:
            return {"error": "No access token"}
        
        debug_results = {}
        
        # Test 1: Basic profile access
        debug_results["profile_test"] = {
            "description": "Testing basic profile access",
        }
        profile = get_linkedin_profile_info(current_user.access_token)
        debug_results["profile_test"]["success"] = bool(profile)
        debug_results["profile_test"]["profile_data"] = profile
        
        # Test 2: Permission check
        debug_results["permissions_test"] = {
            "description": "Checking token permissions",
        }
        permissions = check_linkedin_permissions(current_user.access_token)
        debug_results["permissions_test"]["result"] = permissions
        
        # Test 3: Simple post attempt
        debug_results["simple_post_test"] = {
            "description": "Attempting simple test post",
        }
        test_content = "🤖 Test post from AI automation system - please ignore!"
        post_result = try_simple_text_post(current_user.access_token, test_content)
        debug_results["simple_post_test"]["result"] = post_result
        
        return debug_results
        
    except Exception as e:
        logging.error(f"LinkedIn debug error: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {"error": str(e)}