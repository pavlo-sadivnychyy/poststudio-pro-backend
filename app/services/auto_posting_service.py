import json
import logging
import os
from datetime import datetime, timezone
from typing import List
from sqlalchemy.orm import Session
from app.models.user import User
from app.services.linkedin_service import post_linkedin_content
from app.schemas.post_generator import PostGenerateRequest
import openai

# Set up OpenAI client properly
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_linkedin_post(data: PostGenerateRequest) -> str:
    """Generate LinkedIn post content using OpenAI"""
    prompt = (
        f"Generate a LinkedIn post with the following details:\n"
        f"- Topic: {data.topic}\n"
        f"- Industry: {data.industry}\n"
        f"- Tone: {data.tone}\n"
        f"- Post type: {data.post_type}\n"
        f"- Length (approx words): {data.post_length}\n"
        f"- Include hashtags: {'Yes' if data.include_hashtags else 'No'}\n"
        f"- Include emojis: {'Yes' if data.include_emojis else 'No'}\n\n"
        f"Write a professional, engaging LinkedIn post based on these details. "
        f"Make it authentic and valuable for the audience."
    )
    
    try:
        # Updated to use the newer OpenAI client format
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that writes professional LinkedIn posts. Create engaging, authentic content that provides value to the audience."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=512,
            temperature=0.8,
        )
        
        content = response.choices[0].message.content.strip()
        logging.info(f"Generated LinkedIn post: {content[:100]}...")
        return content
        
    except Exception as e:
        logging.error(f"OpenAI API error: {str(e)}")
        return ""

def should_post_now(user: User) -> bool:
    """Check if it's time to post for this user based on their schedule"""
    try:
        if not user.schedule_settings:
            logging.info(f"User {user.id} has no schedule settings")
            return False
            
        schedule = json.loads(user.schedule_settings)
        current_time = datetime.now(timezone.utc)
        
        if schedule.get('mode') == 'daily':
            # For daily posting, check if we should post at this time
            daily_time = schedule.get('settings', {}).get('dailyTime', '09:00')
            current_hour_minute = current_time.strftime('%H:%M')
            
            # Allow posting within a 15-minute window of the scheduled time
            scheduled_hour, scheduled_minute = daily_time.split(':')
            scheduled_total_minutes = int(scheduled_hour) * 60 + int(scheduled_minute)
            current_total_minutes = current_time.hour * 60 + current_time.minute
            
            time_diff = abs(current_total_minutes - scheduled_total_minutes)
            should_post = time_diff <= 15  # 15-minute window
            
            logging.info(f"User {user.id} daily check: scheduled={daily_time}, current={current_hour_minute}, should_post={should_post}")
            return should_post
            
        elif schedule.get('mode') == 'manual':
            # For manual scheduling, check specific dates and times
            selected_dates = schedule.get('settings', {}).get('selectedDates', {})
            current_date = current_time.strftime('%Y-%m-%d')
            
            if current_date in selected_dates:
                scheduled_times = selected_dates[current_date]
                current_time_str = current_time.strftime('%H:%M')
                
                for scheduled_time in scheduled_times:
                    scheduled_hour, scheduled_minute = scheduled_time.split(':')
                    scheduled_total_minutes = int(scheduled_hour) * 60 + int(scheduled_minute)
                    current_total_minutes = current_time.hour * 60 + current_time.minute
                    
                    time_diff = abs(current_total_minutes - scheduled_total_minutes)
                    if time_diff <= 15:  # 15-minute window
                        logging.info(f"User {user.id} manual check: found matching time {scheduled_time}")
                        return True
            
            logging.info(f"User {user.id} manual check: no matching times for {current_date}")
            return False
            
    except Exception as e:
        logging.error(f"Error checking schedule for user {user.id}: {str(e)}")
        return False
    
    return False

def get_users_to_post(db: Session) -> List[User]:
    """Fetch users who have auto_posting enabled and should post now"""
    users_with_auto_posting = db.query(User).filter(User.auto_posting == True).all()
    users_to_post = []
    
    for user in users_with_auto_posting:
        if should_post_now(user):
            users_to_post.append(user)
    
    return users_to_post

def get_content_template_settings(user: User) -> dict:
    """Get content template settings for the user"""
    try:
        if user.content_templates:
            return json.loads(user.content_templates)
        else:
            # Default template if none exists
            return {
                "story": {
                    "topic": "Professional Growth",
                    "industry": user.industry or "General",
                    "tone": "Professional",  # Use valid tone
                    "post_type": "story",
                    "post_length": 150,
                    "include_hashtags": True,
                    "include_emojis": True
                }
            }
    except Exception as e:
        logging.error(f"Error parsing content templates for user {user.id}: {str(e)}")
        return {}

def get_valid_tone(user_tone: str) -> str:
    """Convert user personality type to valid PostGenerateRequest tone"""
    if not user_tone:
        return "Professional"
    
    tone_mapping = {
        "professional": "Professional",
        "casual": "Casual & Friendly", 
        "friendly": "Casual & Friendly",
        "thought_leader": "Thought Leader",
        "storytelling": "Storytelling",
        "motivational": "Motivational"
    }
    return tone_mapping.get(user_tone.lower(), "Professional")

def run_auto_posting(db: Session):
    """Main function to run auto-posting for all enabled users"""
    try:
        users = get_users_to_post(db)
        logging.info(f"Auto-posting: Found {len(users)} users ready to post")

        for user in users:
            try:
                logging.info(f"Processing auto-posting for user {user.id}")
                
                # Check if user has valid access token
                if not user.access_token:
                    logging.warning(f"User {user.id} has no access token")
                    continue
                
                # Get content template settings
                content_templates = get_content_template_settings(user)
                if not content_templates:
                    logging.warning(f"User {user.id} has no content templates")
                    continue
                
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
                
                logging.info(f"Generating post for user {user.id} with template: {template_name}")
                
                # Generate the content
                content = generate_linkedin_post(post_request)
                if not content:
                    logging.warning(f"Failed to generate post content for user {user.id}")
                    continue
                
                logging.info(f"Generated content for user {user.id}: {content[:100]}...")
                
                # Post to LinkedIn
                success = post_linkedin_content(user.access_token, content)
                if success:
                    logging.info(f"✅ Successfully posted to LinkedIn for user {user.id}")
                else:
                    logging.error(f"❌ Failed to post to LinkedIn for user {user.id}")
            
            except Exception as e:
                logging.error(f"Error in auto-posting for user {user.id}: {str(e)}")
                import traceback
                logging.error(traceback.format_exc())
    
    except Exception as e:
        logging.error(f"Error in run_auto_posting: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())