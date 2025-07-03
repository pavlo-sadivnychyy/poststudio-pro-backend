from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.models.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    linkedin_id = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    access_token = Column(String)
    linkedin_profile = Column(String, nullable=True)

    company = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    
    # Notification preferences
    auto_posting_notifications = Column(Boolean, default=False)
    general_notifications = Column(Boolean, default=False)
    weekly_email_reports = Column(Boolean, default=False)
    
    # === New AI automation settings ===
    auto_posting = Column(Boolean, default=False)
    auto_commenting = Column(Boolean, default=False)
    post_frequency = Column(Integer, default=2)          # Posts per day
    comment_frequency = Column(Integer, default=5)       # Comments per day
    personality_type = Column(String, default='professional')
    engagement_style = Column(String, default='thoughtful')
    industries = Column(String, nullable=True)            # Comma-separated string
    avoid_topics = Column(String, nullable=True)          # Comma-separated string

    # === Content and Schedule settings ===
    content_templates = Column(Text, nullable=True)       # JSON stored as text
    schedule_settings = Column(Text, nullable=True)       # JSON stored as text - NEW FIELD
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())