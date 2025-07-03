import json
import logging
import os
from typing import List
from sqlalchemy.orm import Session
from app.models.user import User
from app.services.linkedin_service import post_linkedin_content  # You'll need this service to post
from app.schemas.post_generator import PostGenerateRequest
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_linkedin_post(data: PostGenerateRequest) -> str:
    prompt = (
        f"Generate a LinkedIn post with the following details:\n"
        f"- Topic: {data.topic}\n"
        f"- Industry: {data.industry}\n"
        f"- Tone: {data.tone}\n"
        f"- Post type: {data.post_type}\n"
        f"- Length (approx words): {data.post_length}\n"
        f"- Include hashtags: {'Yes' if data.include_hashtags else 'No'}\n"
        f"- Include emojis: {'Yes' if data.include_emojis else 'No'}\n\n"
        f"Write a professional, engaging LinkedIn post based on these details."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that writes LinkedIn posts."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=512,
            temperature=0.8,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"OpenAI API error: {str(e)}")
        return ""

def get_users_to_post(db: Session) -> List[User]:
    """Fetch users who have auto_posting enabled"""
    return db.query(User).filter(User.auto_posting == True).all()

def run_auto_posting(db: Session):
    """Main function to run auto-posting for all enabled users"""
    users = get_users_to_post(db)
    logging.info(f"Auto-posting: Found {len(users)} users with active campaigns")

    for user in users:
        try:
            # Load user settings (deserialize JSON)
            content_templates = json.loads(user.content_templates) if user.content_templates else {}
            schedule_settings = json.loads(user.schedule_settings) if user.schedule_settings else {}
            
            # Example: For demo, we pick a template and generate post for it
            # You should customize this logic per your schedule and templates
            post_type = next(iter(content_templates.keys()), "story")
            topic = "Leadership"  # Replace with your own logic, e.g. from templates or avoid_topics etc
            industry = user.industry or "General"
            tone = user.personality_type or "professional"
            
            post_length = 150
            include_hashtags = True
            include_emojis = True
            
            post_request = PostGenerateRequest(
                topic=topic,
                industry=industry,
                tone=tone,
                post_type=post_type,
                post_length=post_length,
                include_hashtags=include_hashtags,
                include_emojis=include_emojis
            )
            
            content = generate_linkedin_post(post_request)
            if not content:
                logging.warning(f"Failed to generate post for user {user.id}")
                continue
            
            # Post content to LinkedIn (using your LinkedIn API service)
            success = post_linkedin_content(user.access_token, content)
            if success:
                logging.info(f"Posted successfully for user {user.id}")
            else:
                logging.error(f"Failed to post LinkedIn content for user {user.id}")
        
        except Exception as e:
            logging.error(f"Error in auto-posting for user {user.id}: {str(e)}")
