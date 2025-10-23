from fastapi import FastAPI
from models.schemas import EventInput
from services.pipeline import run_pipeline
from modules.wbs.router import router as wbs_router

app = FastAPI(title="Event WBS Generator API")

# Register WBS router
app.include_router(wbs_router)


@app.post("/generate-wbs")
def generate_wbs_endpoint(payload: EventInput):
    data = payload.model_dump(exclude_none=True)
    return run_pipeline(data)


@app.get("/")
def root():
    return {"message": "Event WBS Generator API is running"}
