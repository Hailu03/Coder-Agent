"""API endpoints for conversation management."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime
import base64

from ...db.database import get_db
from ...db.models import Conversation, Message, MessageAttachment, User
from ...models.models import (
    ConversationCreate, ConversationResponse, ConversationWithMessages,
    MessageCreate, MessageResponse, AttachmentCreate, AttachmentResponse
)
from ...auth.deps import get_current_user

router = APIRouter()


@router.post("/", response_model=ConversationResponse)
async def create_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new conversation."""
    conversation_id = str(uuid.uuid4())
    
    # Auto-generate title if not provided
    title = conversation.title
    if not title and conversation.task_id:
        title = f"Task Discussion - {conversation.task_id[:8]}"
    elif not title:
        title = f"General Chat - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    db_conversation = Conversation(
        id=conversation_id,
        user_id=current_user.id,
        task_id=conversation.task_id,
        title=title,
        status="active"
    )
    
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    
    return ConversationResponse(
        id=db_conversation.id,
        user_id=db_conversation.user_id,
        task_id=db_conversation.task_id,
        title=db_conversation.title,
        status=db_conversation.status,
        created_at=db_conversation.created_at,
        updated_at=db_conversation.updated_at,
        message_count=0,
        last_message=None
    )


@router.get("/", response_model=List[ConversationResponse])
async def get_conversations(
    task_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all conversations for the current user."""
    query = db.query(Conversation).filter(Conversation.user_id == current_user.id)
    
    if task_id:
        query = query.filter(Conversation.task_id == task_id)
    
    conversations = query.order_by(Conversation.updated_at.desc()).all()
    
    result = []
    for conv in conversations:
        # Get message count and last message
        messages = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.created_at.desc()).all()
        message_count = len(messages)
        last_message = messages[0].content[:100] + "..." if messages and len(messages[0].content) > 100 else (messages[0].content if messages else None)
          # Ensure updated_at is never None (use created_at as fallback)
        updated_at = conv.updated_at or conv.created_at
        
        result.append(ConversationResponse(
            id=conv.id,
            user_id=conv.user_id,
            task_id=conv.task_id,
            title=conv.title,
            status=conv.status,
            created_at=conv.created_at,
            updated_at=updated_at,
            message_count=message_count,
            last_message=last_message
        ))
    
    return result


@router.get("/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific conversation with all messages."""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc()).all()
    message_responses = [
        MessageResponse(
            id=msg.id,
            conversation_id=msg.conversation_id,
            sender=msg.sender,
            agent_type=msg.agent_type,
            content=msg.content,
            message_type=msg.message_type,
            message_metadata=msg.message_metadata,
            created_at=msg.created_at
        ) for msg in messages
    ]
    
    return ConversationWithMessages(
        id=conversation.id,
        user_id=conversation.user_id,
        task_id=conversation.task_id,
        title=conversation.title,
        status=conversation.status,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=message_responses
    )


@router.get("/{conversation_id}/messages/", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all messages for a specific conversation."""
    # Verify conversation exists and belongs to current user
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
      # Get all messages for the conversation
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc()).all()
    
    # Convert to response model
    message_responses = [
        MessageResponse(
            id=msg.id,
            conversation_id=msg.conversation_id,
            sender=msg.sender,
            agent_type=msg.agent_type,
            content=msg.content,
            message_type=msg.message_type,
            message_metadata=msg.message_metadata,
            created_at=msg.created_at
        ) for msg in messages
    ]
    
    return message_responses


@router.post("/{conversation_id}/messages/", response_model=MessageResponse)
async def create_message(
    conversation_id: str,
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a message to a conversation."""
    # Verify conversation exists and belongs to user
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    message_id = str(uuid.uuid4())
    db_message = Message(
        id=message_id,
        conversation_id=conversation_id,
        sender=message.sender,
        agent_type=message.agent_type,
        content=message.content,
        message_type=message.message_type,            message_metadata=message.message_metadata
    )
    
    db.add(db_message)
    
    # Update conversation timestamp
    conversation.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_message)    
    return MessageResponse(
        id=db_message.id,
        conversation_id=db_message.conversation_id,
        sender=db_message.sender,
        agent_type=db_message.agent_type,
        content=db_message.content,
        message_type=db_message.message_type,
        message_metadata=db_message.message_metadata,
        created_at=db_message.created_at
    )


@router.post("/{conversation_id}/messages/{message_id}/attachments/")
async def upload_attachment(
    conversation_id: str,
    message_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload an attachment to a message."""
    # Verify conversation and message exist
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    message = db.query(Message).filter(
        Message.id == message_id,
        Message.conversation_id == conversation_id
    ).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Read file data
    file_data = await file.read()
    
    # Check file size (limit to 10MB for now)
    if len(file_data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")
    
    attachment_id = str(uuid.uuid4())
    
    db_attachment = MessageAttachment(
        id=attachment_id,
        message_id=message_id,
        file_name=file.filename,
        file_type=file.content_type,
        file_size=len(file_data),
        file_data=file_data
    )
    
    db.add(db_attachment)
    db.commit()
    db.refresh(db_attachment)
    
    return {
        "id": db_attachment.id,
        "message_id": db_attachment.message_id,
        "file_name": db_attachment.file_name,
        "file_type": db_attachment.file_type,
        "file_size": db_attachment.file_size,
        "created_at": db_attachment.created_at
    }


@router.get("/{conversation_id}/messages/{message_id}/attachments/{attachment_id}")
async def get_attachment(
    conversation_id: str,
    message_id: str,
    attachment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get an attachment file."""
    # Verify ownership chain
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    attachment = db.query(MessageAttachment).filter(
        MessageAttachment.id == attachment_id,
        MessageAttachment.message_id == message_id
    ).first()
    
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    
    # Return file as base64 for images, or raw data for other files
    if attachment.file_type.startswith('image/'):
        file_data_b64 = base64.b64encode(attachment.file_data).decode('utf-8')
        return {
            "id": attachment.id,
            "file_name": attachment.file_name,
            "file_type": attachment.file_type,
            "file_size": attachment.file_size,
            "data": f"data:{attachment.file_type};base64,{file_data_b64}"
        }
    else:
        from fastapi.responses import Response
        return Response(
            content=attachment.file_data,
            media_type=attachment.file_type,
            headers={"Content-Disposition": f"attachment; filename={attachment.file_name}"}
        )


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a conversation and all its messages."""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    db.delete(conversation)
    db.commit()
    
    return {"message": "Conversation deleted successfully"}


@router.put("/{conversation_id}/title")
async def update_conversation_title(
    conversation_id: str,
    title: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update conversation title."""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation.title = title
    conversation.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Title updated successfully", "title": title}
