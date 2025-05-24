from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, LargeBinary
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
    
    # Relationships
    tasks = relationship("Task", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")


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
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    documents = relationship("Document", back_populates="task", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="task")


class Document(Base):
    __tablename__ = "documents"
    id = Column(String(36), primary_key=True)  # UUID string
    task_id = Column(String(36), ForeignKey("tasks.id"), index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    task = relationship("Task", back_populates="documents")


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True)  # UUID string
    user_id = Column(Integer, ForeignKey("users.id"))
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=True)  # Optional, can be standalone chat
    title = Column(String(255), nullable=True)  # Auto-generated or user-defined
    status = Column(String(20), default="active")  # active, archived
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    task = relationship("Task", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True)  # UUID string
    conversation_id = Column(String(36), ForeignKey("conversations.id"))
    sender = Column(String(20))  # 'user', 'agent'
    agent_type = Column(String(50), nullable=True)  # 'planner', 'researcher', 'developer', 'tester', 'system'
    content = Column(Text)
    message_type = Column(String(50), default="text")  # 'text', 'code', 'image', 'file'
    message_metadata = Column(JSON, nullable=True)  # For storing additional data like image info, code language, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    conversation = relationship("Conversation", back_populates="messages")


class MessageAttachment(Base):
    __tablename__ = "message_attachments"
    
    id = Column(String(36), primary_key=True)  # UUID string
    message_id = Column(String(36), ForeignKey("messages.id"))
    file_name = Column(String(255))
    file_type = Column(String(100))  # 'image/png', 'image/jpeg', etc.
    file_size = Column(Integer)
    file_data = Column(LargeBinary, nullable=True)  # Store small files directly
    file_path = Column(String(500), nullable=True)  # Path to file storage for larger files
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    message = relationship("Message")
