from fastapi import APIRouter, HTTPException, Depends
from app.schemas.post_generator import PostGenerateRequest
import os
import openai

router = APIRouter()

# Initialize OpenAI client once
openai.api_key = os.getenv("OPENAI_API_KEY")

def build_prompt(data: PostGenerateRequest) -> str:
    # Build a prompt string for the OpenAI model, you can customize this as needed
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
    return prompt

@router.post("/generate-post")
async def generate_post(data: PostGenerateRequest):
    prompt = build_prompt(data)
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4o-mini",  # or your preferred model
            messages=[
                {"role": "system", "content": "You are a helpful assistant that writes LinkedIn posts."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=512,
            temperature=0.8,
        )
        text = response.choices[0].message.content.strip()
        return {"generated_post": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
