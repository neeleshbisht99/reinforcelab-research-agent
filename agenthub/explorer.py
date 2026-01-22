import os
import asyncio
from typing import List, Tuple
from parallel import Parallel


class ExplorerAgent:
    def __init__(self):
        self.parallel = Parallel(
            api_key=os.environ["PARALLEL_API_KEY"],
            default_headers={"parallel-beta": "search-extract-2025-10-10"},
        )
        self.betas = ["search-extract-2025-10-10"]

    def tool_search(
        self,
        objective: str,
        search_queries=None,
        max_results: int = 10,
        max_chars_per_result: int = 10,
    ):
        resp = self.parallel.beta.search(
            objective=objective,
            search_queries=search_queries or [],
            max_results=max_results,
            excerpts={"max_chars_per_result": max_chars_per_result},
        )
        return resp.results

    def tool_extract(
        self,
        urls: List[str],
        objective: str,
        max_chars_per_result: int = 1000,
    ):
        resp = self.parallel.beta.extract(
            betas=self.betas,
            urls=urls,
            objective=objective,
            excerpts={"max_chars_per_result": max_chars_per_result},
            full_content=False,
        )
        return resp.results

    def get_field(self, obj, name, default=None):
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)

    def search_and_extract(
        self,
        task_text: str,
        agent_tag: str,
        main_prompt: str,
        max_urls: int = 5,
    ) -> Tuple[dict, list]:
        search_results = self.tool_search(
            objective=task_text, max_results=max_urls
        )

        urls = []
        for r in search_results:
            u = self.get_field(r, "url")
            if u:
                urls.append(u)

        urls = urls[:max_urls]
        log_item = {
            "agent": agent_tag,
            "objective": task_text,
            "urls": urls,
        }

        if not urls:
            return log_item, []

        extract_results = self.tool_extract(urls=urls, objective=main_prompt)

        evidence = []
        for r in extract_results:
            url = self.get_field(r, "url")
            excerpts = self.get_field(r, "excerpts", []) or []
            for ex in excerpts:
                evidence.append(
                    {"agent": agent_tag, "url": url, "quote": ex}
                )

        return log_item, evidence

    def dedup_evidence(self, state: dict):
        seen = set()
        deduped = []
        for e in state["evidence"]:
            key = (e.get("url"), e.get("quote"))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(e)
        state["evidence"] = deduped

    async def run(self, state: dict):
        prompt = state["prompt"]
        tasks = state.get("tasks", []) or []

        jobs = []
        for t in tasks:
            objective = t.get("task", "").strip()
            tag = t.get("tag", "general").strip()
            if not objective:
                continue
            jobs.append(
                asyncio.to_thread(
                    self.search_and_extract, objective, tag, prompt
                )
            )

        results = await asyncio.gather(*jobs)

        for item in results:
            if not item:
                continue
            log_item, ev = item
            if log_item:
                state["search_log"].append(log_item)
            if ev:
                state["evidence"].extend(ev)

        self.dedup_evidence(state)