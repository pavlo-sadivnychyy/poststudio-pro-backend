from typing import Dict, List
from pydantic import BaseModel

class ContentTemplate(BaseModel):
    active: bool
    posts: int

class ContentSettingsRequest(BaseModel):
    content_templates: Dict[str, ContentTemplate]

class ContentSettingsResponse(BaseModel):
    content_templates: Dict[str, ContentTemplate]
