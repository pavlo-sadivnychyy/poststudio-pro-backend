# app/schemas/post_generator.py

from pydantic import BaseModel
from typing import Optional, Literal

class PostGenerateRequest(BaseModel):
    topic: str
    short_description: Optional[str] = None
    industry: str
    tone: Literal['Professional', 'Casual & Friendly', 'Thought Leader', 'Storytelling', 'Motivational']
    post_type: Literal['story', 'tips', 'announcement', 'question', 'achievement', 'industry']
    post_length: int
    include_hashtags: bool
    include_emojis: bool
