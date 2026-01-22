import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

@dataclass
class SafetyResult:
    blocked: bool
    reason: str
    matches: List[Dict]

def blocked_prompt_response(res: SafetyResult) -> Dict:
    return {
        "final_report": (
            "# Request Blocked\n\n"
            "Your prompt triggered our safety checks and was not executed.\n\n"
            f"**Reason:** {res.reason}\n\n"
            "Please rewrite the request without system overrides, tool abuse, "
            "or instruction manipulation."
        ),
        "safety": {
            "blocked": True,
            "reason": res.reason,
            "matches": res.matches,
        },
    }

class PromptInjectionGuard:
    def __init__(self):
        self.prompt_patterns = [
            ("ignore_prev", r"ignore (all|any|previous) (instructions|directions)"),
            ("system_prompt", r"(reveal|show|print).{0,40}(system prompt|developer message|hidden prompt)"),
            ("roleplay_override", r"you are (now|no longer) (chatgpt|an ai|the system)"),
            ("tool_abuse", r"(run|execute|call) (a tool|tools|function|functions)"),
            ("data_exfil", r"(api key|password|secret|token|credentials)"),
            ("jailbreak", r"(jailbreak|do anything now|dan)"),
        ]

        self.plan_patterns = re.compile(
            r"(ignore (all|previous) instructions|system prompt|developer message|"
            r"api key|password|secret|token|jailbreak|do anything now|"
            r"\b(run|execute|call)\b.+\b(tool|function)\b)",
            re.IGNORECASE,
        )

    def _scan_text(self, text: str) -> List[Dict]:
        hits = []
        if not text:
            return hits
        t = text.lower()
        for name, pat in self.prompt_patterns:
            if re.search(pat, t):
                hits.append({"pattern": name, "snippet": text[:200]})
        return hits

    def validate_prompt(self, prompt: str) -> SafetyResult:
        matches = ([{"where": "prompt", **m} for m in self._scan_text(prompt)])

        if matches:
            return SafetyResult(
                blocked=True,
                reason="Possible prompt-injection detected in prompt/evidence. Refusing to follow untrusted instructions.",
                matches=matches[:20],
            )

        return SafetyResult(blocked=False, reason="", matches=[])

    

    def validate_planner(self, data: dict) -> SafetyResult:
        if not isinstance(data, dict):
            return SafetyResult(True, "Planner output is not a dict.", [])

        tasks = data.get("tasks")
        if not isinstance(tasks, list) or not tasks:
            return SafetyResult(True, "Planner produced no tasks.", [])

        for i, t in enumerate(tasks):
            if not isinstance(t, dict):
                return SafetyResult(True, "Planner task is not a dict.", [{"idx": i}])

            task = (t.get("task") or "").strip()
            tag = t.get("tag")

            if not task or tag not in {"research", "industry", "general"}:
                return SafetyResult(True, "Planner produced invalid task format.", [{"idx": i}])

            if self.plan_patterns.search(task):
                return SafetyResult(True, "Planner task contains unsafe instructions.", [
                    {"idx": i, "snippet": task[:200]}
                ])

        return SafetyResult(False, "", [])