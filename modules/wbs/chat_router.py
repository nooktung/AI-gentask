
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid

from services.chat_processor import ChatProcessor

router = APIRouter(prefix="/api/chat", tags=["Chat WBS"])


class ChatInput(BaseModel):
    message: str
    session_id: Optional[str] = None


# Global chat processor instance
chat_processor = ChatProcessor()


@router.post("/message")
async def send_message(chat_input: ChatInput) -> Dict[str, Any]:
    """
    Send message to AI assistant
    
    Returns exact format:
    {
        "session_id": str,
        "message": str,  # AI response
        "extracted_info": {...},  # Only when generating WBS
        "epics_task": [...],      # Only when generating WBS
        "tasks": [...],           # Only when generating WBS
        "departments": {...},     # Only when generating WBS
        "risks": {...}            # Only when generating WBS
    }
    """
    try:
        # Generate session_id if not provided
        session_id = chat_input.session_id or str(uuid.uuid4())
        
        # Process message
        result = chat_processor.process_message(
            message=chat_input.message,
            session_id=session_id
        )
        
        # Build response with session_id
        response = {
            "session_id": session_id,
            "message": result.get("message", ""),
        }
        
        # Add WBS data if available (when event planning is complete)
        if "extracted_info" in result:
            response["extracted_info"] = result["extracted_info"]
        
        if "epics_task" in result:
            response["epics_task"] = result["epics_task"]
        
        if "tasks" in result:
            response["tasks"] = result["tasks"]
        
        if "departments" in result:
            response["departments"] = result["departments"]
        
        if "risks" in result:
            response["risks"] = result["risks"]
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý: {str(e)}")


@router.get("/sessions/{session_id}/history")
async def get_conversation_history(session_id: str):
    """Get conversation history for a session"""
    try:
        history = chat_processor.get_session_history(session_id)
        return {
            "session_id": session_id,
            "history": history,
            "total_messages": len(history)
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clear conversation history for a session"""
    try:
        chat_processor.clear_session(session_id)
        return {"message": f"Session {session_id} đã được xóa"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/sessions")
async def list_active_sessions():
    """List all active sessions"""
    sessions = chat_processor.list_active_sessions()
    return {
        "sessions": sessions,
        "total": len(sessions)
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0",
        "features": [
            "conversational_ai",
            "context_switching",
            "rag_queries",
            "venue_tier_scaling",
            "risk_assessment"
        ]
    }