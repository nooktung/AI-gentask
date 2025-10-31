from fastapi import FastAPI
from models.schemas import EventInput
from services.pipeline import run_pipeline
from modules.wbs.router import router as wbs_router
from modules.wbs.chat_router import router as chat_router

app = FastAPI(title="Event WBS Generator API", version="2.0.0")

# Register routers
app.include_router(wbs_router)
app.include_router(chat_router)


@app.post("/generate-wbs")
def generate_wbs_endpoint(payload: EventInput):
    data = payload.model_dump(exclude_none=True)
    return run_pipeline(data)


@app.get("/")
def root():
    return {
        "message": "Event WBS Generator API is running",
        "features": [
            "Traditional JSON input WBS generation",
            "Natural language chat interface",
            "Conversation memory",
            "Enhanced Knowledge Base"
        ],
        "endpoints": {
            "traditional": "/api/wbs/generate",
            "chat": "/api/chat/message",
            "docs": "/docs"
        }
    }
