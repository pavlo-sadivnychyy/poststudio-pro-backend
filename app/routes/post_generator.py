from fastapi import APIRouter, HTTPException, Depends
from app.schemas.post_generator import PostGenerateRequest
import os
from openai import OpenAI

router = APIRouter()

# Initialize OpenAI client with the new v1.0+ syntax
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def build_prompt(data: PostGenerateRequest) -> str:
    """Build a detailed prompt for generating LinkedIn posts"""
    
    # Enhanced prompt with better instructions
    prompt = f"""Create a professional LinkedIn post with these specifications:

CONTENT REQUIREMENTS:
- Topic: {data.topic}
- Industry: {data.industry}
- Tone: {data.tone}
- Post Type: {data.post_type}
- Target Length: Approximately {data.post_length} words
- Include Hashtags: {'Yes' if data.include_hashtags else 'No'}
- Include Emojis: {'Yes' if data.include_emojis else 'No'}

POST TYPE GUIDELINES:
- story: Share a personal experience with lessons learned
- tips: Provide actionable advice and insights
- announcement: Make a professional announcement or update
- question: Ask an engaging question to start a conversation
- achievement: Celebrate a milestone or accomplishment
- industry: Comment on industry trends or news

TONE GUIDELINES:
- Professional: Formal, authoritative, business-focused
- Casual & Friendly: Conversational, approachable, warm
- Thought Leader: Insightful, forward-thinking, analytical
- Storytelling: Narrative-driven, engaging, personal
- Motivational: Inspiring, uplifting, encouraging

FORMATTING REQUIREMENTS:
- Use line breaks for readability
- Make it engaging and authentic
- Include a call-to-action when appropriate
- Keep within the specified word count
{"- Include relevant hashtags at the end" if data.include_hashtags else "- Do not include hashtags"}
{"- Use emojis appropriately throughout the post" if data.include_emojis else "- Do not use emojis"}

Generate a compelling LinkedIn post that follows these guidelines."""

    return prompt

@router.post("/generate-post")
async def generate_post(data: PostGenerateRequest):
    """Generate a LinkedIn post using OpenAI"""
    
    try:
        prompt = build_prompt(data)
        
        # Use the new OpenAI v1.0+ client syntax
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # or "gpt-3.5-turbo" for faster/cheaper option
            messages=[
                {
                    "role": "system", 
                    "content": "You are a professional LinkedIn content creator who writes engaging, authentic posts that drive engagement and build professional networks. Always follow the specific requirements provided."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=600,  # Increased for longer posts
            temperature=0.7,  # Balanced creativity
            top_p=1,
            frequency_penalty=0.1,  # Reduce repetition
            presence_penalty=0.1    # Encourage variety
        )
        
        generated_text = response.choices[0].message.content.strip()
        
        return {
            "generated_post": generated_text,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
        
    except Exception as e:
        # More detailed error handling
        error_message = str(e)
        
        if "insufficient_quota" in error_message:
            raise HTTPException(
                status_code=402, 
                detail="OpenAI API quota exceeded. Please check your billing."
            )
        elif "invalid_api_key" in error_message:
            raise HTTPException(
                status_code=401, 
                detail="Invalid OpenAI API key."
            )
        elif "rate_limit" in error_message:
            raise HTTPException(
                status_code=429, 
                detail="Rate limit exceeded. Please try again later."
            )
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"OpenAI API error: {error_message}"
            )