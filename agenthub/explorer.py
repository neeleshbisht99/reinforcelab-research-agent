import asyncio
from typing import List, Tuple

from clients.parallel_client import ParallelClient
from core.config import Settings


class ExplorerAgent:
    def __init__(self, parallel_client: ParallelClient, settings: Settings):
        self.parallel = parallel_client
        self.settings = settings

    def get_field(self, obj, name, default=None):
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)

    def search_and_extract(
        self,
        task_text: str,
        agent_tag: str,
        main_prompt: str,
        max_urls: int | None = None,
    ) -> Tuple[dict, list]:
        if max_urls is None:
            max_urls = self.settings.max_urls_per_task

        search_results = self.parallel.search(
            objective=task_text,
            max_results=max_urls,
            max_chars=self.settings.max_search_excerpt_chars,
        )

        urls = []
        for r in search_results:
            u = self.get_field(r, "url")
            if u:
                urls.append(u)

        urls = urls[:max_urls]
        log_item = {"agent": agent_tag, "objective": task_text, "urls": urls}

        if not urls:
            return log_item, []

        extract_results = self.parallel.extract(
            urls=urls,
            objective=main_prompt,
            max_chars=self.settings.max_extract_chars,
        )

        evidence = []
        for r in extract_results:
            url = self.get_field(r, "url")
            excerpts = self.get_field(r, "excerpts", []) or []
            for ex in excerpts:
                evidence.append({"agent": agent_tag, "url": url, "quote": ex})
                if len(evidence) >= self.settings.max_evidence_per_task:
                    return log_item, evidence

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
            objective = (t.get("task") or "").strip()
            tag = (t.get("tag") or "general").strip()
            if not objective:
                continue
            jobs.append(asyncio.to_thread(self.search_and_extract, objective, tag, prompt))

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