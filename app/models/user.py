# app/models/user.py
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
    auto_posting_notifications = Column(Boolean, default=True)
    general_notifications = Column(Boolean, default=True)
    weekly_email_reports = Column(Boolean, default=True)
    
    # === AI automation settings ===
    auto_posting = Column(Boolean, default=True)
    auto_commenting = Column(Boolean, default=True)
    post_frequency = Column(Integer, default=2)
    comment_frequency = Column(Integer, default=5)
    personality_type = Column(String, default='professional')
    engagement_style = Column(String, default='thoughtful')
    industries = Column(String, nullable=True)
    avoid_topics = Column(String, nullable=True)

    # === Content & schedule settings ===
    content_templates = Column(Text, nullable=True)
    schedule_settings = Column(Text, nullable=True)
    
    # === Subscription fields ===
    subscription_active  = Column(Boolean, default=False)
    subscription_plan    = Column(String, nullable=True)
    subscription_expires = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
