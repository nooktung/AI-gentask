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
    
    UPDATED: Returns 'departments' with full task info (no separate 'tasks' field)
    
    Returns format with clear state indication:
    - state: "conversation" | "planning_partial" | "planning_complete"
    - message: AI response text
    - extracted_info: Extracted event info (if state != "conversation")
    - wbs: Full WBS data with 'departments' containing full tasks (only if state == "planning_complete")
    """
    try:
        # Generate session_id if not provided
        session_id = chat_input.session_id or str(uuid.uuid4())
        
        # Process message
        result = chat_processor.process_message(
            message=chat_input.message,
            session_id=session_id
        )
        
        # Determine state based on result content (backward compatible)
        state = result.get("state")
        if not state:
            # Check for full WBS with departments containing tasks
            has_wbs = "departments" in result and any(result.get("departments", {}).values())
            if has_wbs:
                state = "planning_complete"
            elif "extracted_info" in result:
                state = "planning_partial"
            else:
                state = "conversation"
        
        # Build base response
        response = {
            "session_id": session_id,
            "state": state,
            "message": result.get("message", ""),
        }
        
        # Add extracted info if available (both partial and complete states)
        if "extracted_info" in result and state != "conversation":
            response["extracted_info"] = result["extracted_info"]
        
        # Add full WBS data ONLY when planning is complete
        if state == "planning_complete":
            # Ensure all WBS components are present
            if all(key in result for key in ["epics_task", "departments", "risks"]):
                response["wbs"] = {
                    "epics_task": result["epics_task"],
                    "departments": result["departments"],  # Contains full task info
                    "risks": result["risks"],
                }
                
                # Optional: Add RAG insights if available
                if "rag_insights" in result:
                    response["rag_insights"] = result["rag_insights"]
            elif "wbs" in result and isinstance(result["wbs"], dict):
                # Some versions return a nested wbs object directly
                response["wbs"] = result["wbs"]
            else:
                # Incomplete WBS - should not happen, but handle gracefully
                response["state"] = "error"
                response["error"] = "WBS generation incomplete"
        
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
        "version": "2.0",
        "features": [
            "conversational_ai",
            "context_switching",
            "rag_queries",
            "venue_tier_scaling",
            "risk_assessment",
            "state_management",
            "unified_departments_format"  # NEW: departments contain full task info
        ],
        "response_format": {
            "note": "No separate 'tasks' field - all task info is in 'departments'"
        }
    }