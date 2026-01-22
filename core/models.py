from typing import Any, Dict, List


def init_state(prompt: str) -> Dict[str, Any]:
    return {
        "prompt": prompt,
        "plan": [],
        "tasks": [],
        "search_log": [],     # list of {agent, objective, urls}
        "evidence": [],       # list of {agent, url, excerpts}
        "summary_structured": {},
        "final_report": "",
    }