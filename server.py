import os
import time
import asyncio
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from main import (
    init_state,
    planner_agent,
    run_exploration,
    summarizer_agent,
    markdown_agent,
)

app = FastAPI(title="Research Agent API")


class ResearchRequest(BaseModel):
    prompt: str


@app.get("/health")
def health():
    return {"ok": True}


async def run_pipeline(prompt: str) -> Dict[str, Any]:
    state = init_state(prompt)

    planner_agent(state)
    await run_exploration(state)
    summarizer_agent(state)
    markdown_agent(state)

    return state


@app.post("/research")
async def research(req: ResearchRequest):
    prompt = (req.prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")

    t0 = time.time()
    try:
        state = await run_pipeline(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "final_report": state.get("final_report", ""),
        "summary_structured": state.get("summary_structured", {}),
        "plan": state.get("plan", []),
        "tasks": state.get("tasks", []),
        "search_log": state.get("search_log", []),
        "evidence_count": len(state.get("evidence", []) or []),
        "took_seconds": round(time.time() - t0, 2),
    }
