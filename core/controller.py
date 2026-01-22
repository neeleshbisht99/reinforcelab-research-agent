from typing import Any, Dict
import logging
import time

from core.models import init_state
from core.config import load_settings, OpenAIConfig, ParallelConfig

from clients.openai_client import OpenAIClient
from clients.parallel_client import ParallelClient

from agenthub.planner import PlannerAgent
from agenthub.explorer import ExplorerAgent
from agenthub.summarizer import SummarizerAgent
from agenthub.markdown import MarkdownAgent
from core.safety import PromptInjectionGuard, blocked_prompt_response

logger = logging.getLogger("research")
logging.basicConfig(level=logging.INFO)

class ResearchController:
    def __init__(self):
        self.settings = load_settings()

        self.openai_client = OpenAIClient(
            model=self.settings.openai_model
        )

        self.parallel_client = ParallelClient(
            beta_version=ParallelConfig.BETA_VERSION
        )

        self.planner = PlannerAgent(
            client=self.openai_client
        )

        self.explorer = ExplorerAgent(
            parallel_client=self.parallel_client,
            settings=self.settings,
        )

        self.summarizer = SummarizerAgent(
            client=self.openai_client,
            settings=self.settings,
        )

        self.markdown = MarkdownAgent(self.settings)
        self.guard = PromptInjectionGuard()

    async def run_pipeline(self, prompt: str) -> Dict[str, Any]:
        res = self.guard.validate_prompt(prompt)
        if res.blocked:
            return blocked_prompt_response(res)

        state = init_state(prompt)

        timings = {}
        t = time.time()

        self.planner.run(state)
        plan_res = self.guard.validate_planner(state)
        if plan_res.blocked:
            return blocked_prompt_response(plan_res)
        timings["planner_s"] = round(time.time() - t, 3)

        t = time.time()
        await self.explorer.run(state)
        timings["explorer_s"] = round(time.time() - t, 3)

        t = time.time()
        self.summarizer.run(state)
        timings["summarizer_s"] = round(time.time() - t, 3)

        t = time.time()
        self.markdown.run(state)
        timings["markdown_s"] = round(time.time() - t, 3)

        logger.info({
            "timings": timings,
            "tasks": len(state.get("tasks", [])),
            "evidence": len(state.get("evidence", [])),
            "blocked": state.get("safety", {}).get("blocked", False),
        })

        return state