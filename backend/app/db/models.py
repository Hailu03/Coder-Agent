from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    full_name = Column(String(100))
    avatar = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship with Task model
    tasks = relationship("Task", back_populates="user")


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String(36), primary_key=True)  # UUID string
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20), index=True)  # PENDING, PROCESSING, COMPLETED, FAILED
    requirements = Column(Text)
    language = Column(String(50))
    additional_context = Column(Text, nullable=True)
    solution = Column(JSON, nullable=True)
    explanation = Column(Text, nullable=True)
    code_files = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    detailed_status = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship with User model
    user = relationship("User", back_populates="tasks")