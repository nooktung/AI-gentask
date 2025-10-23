from fastapi import APIRouter
from models.schemas import EventInput
from services.pipeline import run_pipeline

router = APIRouter(prefix="/api/wbs", tags=["WBS"])


@router.post("/generate")
async def generate_wbs_endpoint(event_input: EventInput):
    """
    Generate WBS using hybrid rule + LLM, returning simplified output format.
    """
    data = event_input.model_dump(exclude_none=True)
    return run_pipeline(data)
