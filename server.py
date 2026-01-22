import time
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from core.controller import ResearchController

app = FastAPI(title="Research Agent API")
controller = ResearchController()


class ResearchRequest(BaseModel):
    prompt: str


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/research")
async def research(req: ResearchRequest):
    prompt = (req.prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")

    t0 = time.time()
    try:
        state = await controller.run_pipeline(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    state["took_seconds"] = round(time.time() - t0, 2)
    return {"final_report": state.get("final_report", ""), **state}