from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import openai
import os

router = APIRouter()

openai.api_key = os.getenv("OPENAI_API_KEY", "your-openai-key")

class PostRequest(BaseModel):
    user_id: int
    industry: str
    topic: str
    tone: str = "professional"

class CommentRequest(BaseModel):
    user_id: int
    post_text: str
    tone: str = "thoughtful"

@router.post("/post")
def generate_post(data: PostRequest):
    try:
        prompt = f"Write a {data.tone} LinkedIn post for someone in the {data.industry} industry about {data.topic}."
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a LinkedIn post generator."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )
        return {"post": response.choices[0].message.content.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/comment")
def generate_comment(data: CommentRequest):
    try:
        prompt = f"""Write a {data.tone} comment in response to this LinkedIn post:

\"\"\"{data.post_text}\"\"\"
"""
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional LinkedIn commenter."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150
        )
        return {"comment": response.choices[0].message.content.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
