from typing import Any, Dict

from core.models import init_state
from agenthub.planner import planner_agent
from agenthub.explorer import run_exploration
from agenthub.summarizer import summarizer_agent
from agenthub.markdown import markdown_agent


class ResearchController:
    async def run_pipeline(self, prompt: str) -> Dict[str, Any]:
        state = init_state(prompt)

        planner_agent(state)
        await run_exploration(state)
        summarizer_agent(state)
        markdown_agent(state)

        return state