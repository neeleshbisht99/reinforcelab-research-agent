import json

class SummarizerAgent:
    def __init__(self, client, model):
        self.client = client
        self.model = model

    def run(self, state):
        prompt = state["prompt"]
        evidence = state.get("evidence", []) or []

        MAX_ITEMS = 80  # get from config later
        MAX_CHARS = 18000  # get from config later

        trimmed = []
        total = 0
        for e in evidence[:MAX_ITEMS]:
            item = {
                "agent": e.get("agent", ""),
                "url": e.get("url", ""),
                "quote": (e.get("quote", "") or "").strip()
            }
            s = json.dumps(item, ensure_ascii=False)
            if total + len(s) > MAX_CHARS:
                break
            trimmed.append(item)
            total += len(s)

        system = (
            "You are a careful research synthesizer.\n"
            "Use ONLY the provided evidence.\n"
            "Do not create or invent facts.\n"
            "Prefer concrete claims with citations."
        )

        user = f"""
        Topic:
        {prompt}

        Evidence (JSON list of {{agent,url,quote}}):
        {json.dumps(trimmed, ensure_ascii=False, indent=2)}

        Produce ONLY valid JSON (no markdown, no extra text) with this schema:

        {{
        "title": "short title",
        "main_summary": "2-5 sentences max",
        "key_insights": [
            {{"insight": "1-2 sentence insight", "sources": ["url1","url2"]}}
        ],
        "sections": [
            {{
            "heading": "Section heading",
            "bullets": [
                {{"point": "1-2 sentence point", "sources": ["url"]}}
            ]
            }}
        ],
        "tables": [
            {{
            "title": "Table title",
            "columns": ["Col1","Col2","Col3"],
            "rows": [
                ["...", "...", "..."]
            ],
            "sources": ["url1"]
            }}
        ],
        "references": ["unique_url1", "unique_url2"]
        }}

        Rules:
        - Every insight/point must include at least 1 source URL from the evidence list.
        - Only use URLs present in evidence.
        - If evidence is weak, say so in main_summary and create a section named "Limitations".
        """.strip()

        resp = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )

        text = (resp.output_text or "").strip()
        try:
            state["summary_structured"] = json.loads(text)
        except Exception:
            refs = []
            for e in trimmed:
                if e.get("url"): refs.append(e["url"])
            refs = list(dict.fromkeys(refs))
            state["summary_structured"] = {
                "title": prompt[:80],
                "main_summary": "Evidence collected, but summarization JSON parsing failed.",
                "key_insights": [],
                "sections": [{"heading": "findings", "bullets": []}],
                "tables": [],
                "references": refs[:30],
            }