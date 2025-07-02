from pydantic import BaseModel
from typing import Literal

class PostGenerateRequest(BaseModel):
    topic: str
    industry: str
    tone: Literal['Professional', 'Casual & Friendly', 'Thought Leader', 'Storytelling', 'Motivational']
    post_type: Literal['story', 'tips', 'announcement', 'question', 'achievement', 'industry']
    post_length: int
    include_hashtags: bool
    include_emojis: bool
