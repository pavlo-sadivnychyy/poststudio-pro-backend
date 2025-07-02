from pydantic import BaseModel
from typing import List, Optional

class AutomationSettingsRequest(BaseModel):
    auto_posting: Optional[bool]
    auto_commenting: Optional[bool]
    post_frequency: Optional[int]
    comment_frequency: Optional[int]
    personality_type: Optional[str]
    engagement_style: Optional[str]
    industries: Optional[List[str]]
    avoid_topics: Optional[List[str]]

class AutomationSettingsResponse(BaseModel):
    auto_posting: bool
    auto_commenting: bool
    post_frequency: int
    comment_frequency: int
    personality_type: str
    engagement_style: str
    industries: List[str]
    avoid_topics: List[str]
