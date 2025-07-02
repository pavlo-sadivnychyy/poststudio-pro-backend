from typing import Dict, List
from pydantic import BaseModel

class ContentTemplate(BaseModel):
    active: bool
    posts: int

class ScheduleSettings(BaseModel):
    timezone: str
    optimal_times: bool
    custom_times: List[str]

class ContentSettingsRequest(BaseModel):
    content_templates: Dict[str, ContentTemplate]
    schedule_settings: ScheduleSettings

class ContentSettingsResponse(BaseModel):
    content_templates: Dict[str, ContentTemplate]
    schedule_settings: ScheduleSettings
