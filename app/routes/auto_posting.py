# Add this debug endpoint to your app/routes/auto_posting.py

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
            from app.services.auto_posting_service import should_post_now
            should_post = should_post_now(current_user)
            debug_info["checks"]["should_post_now"] = f"{'✅' if should_post else '❌'} Should post now: {should_post}"
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
        
        # Generate test content
        test_request = PostGenerateRequest(
            topic="Test Post",
            industry=current_user.industry or "Technology",
            tone=current_user.personality_type or "professional",
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