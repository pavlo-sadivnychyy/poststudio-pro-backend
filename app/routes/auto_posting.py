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

@router.get("/auto-posting/linkedin-profile-test")
def test_linkedin_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Test LinkedIn API access"""
    try:
        from app.services.linkedin_service import get_linkedin_profile_info
        
        if not current_user.access_token:
            return {"error": "No access token"}
        
        profile = get_linkedin_profile_info(current_user.access_token)
        return {
            "success": bool(profile),
            "profile": profile,
            "person_urn": f"urn:li:person:{profile.get('id')}" if profile else None
        }
        
    except Exception as e:
        return {"error": str(e)}