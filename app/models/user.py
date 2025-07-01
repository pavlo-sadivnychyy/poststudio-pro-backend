# app/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime
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
    
    # Add missing columns
    company = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    
    # Notification preferences
    auto_posting_notifications = Column(Boolean, default=True)
    general_notifications = Column(Boolean, default=True)
    weekly_email_reports = Column(Boolean, default=True)
    
    # Optional: Add timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())