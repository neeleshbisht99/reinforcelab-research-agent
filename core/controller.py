from typing import Any, Dict

from core.models import init_state
from core.config import load_settings, OpenAIConfig, ParallelConfig

from clients.openai_client import OpenAIClient
from clients.parallel_client import ParallelClient

from agenthub.planner import PlannerAgent
from agenthub.explorer import ExplorerAgent
from agenthub.summarizer import SummarizerAgent
from agenthub.markdown import MarkdownAgent


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
            client=self.openai_client
        )

        self.markdown = MarkdownAgent(self.settings)

    async def run_pipeline(self, prompt: str) -> Dict[str, Any]:
        state = init_state(prompt)

        self.planner.run(state)
        await self.explorer.run(state)
        self.summarizer.run(state)
        self.markdown.run(state)

        return state