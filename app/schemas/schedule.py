# app/schemas/schedule.py
from pydantic import BaseModel
from typing import Dict, List, Literal, Union

class DailyScheduleSettings(BaseModel):
    dailyTime: str  # e.g., "09:00"

class ManualScheduleSettings(BaseModel):
    selectedDates: Dict[str, List[str]]  # e.g., {"2024-03-15": ["09:00", "14:00"]}

class ScheduleSettingsRequest(BaseModel):
    mode: Literal["daily", "manual"]
    timezone: str  # e.g., "UTC+2"
    settings: Union[DailyScheduleSettings, ManualScheduleSettings]

class ScheduleSettingsResponse(BaseModel):
    mode: str
    timezone: str
    settings: Dict  # Flexible dict to handle both daily and manual settings

class ScheduleUpdateResponse(BaseModel):
    message: str
    schedule_summary: str