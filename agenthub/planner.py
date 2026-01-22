import json

class PlannerAgent:
    def __init__(self, client):
        self.client = client

    def run(self, state):
        prompt = state["prompt"]
        system = "You are a planner for a research agent."
        user = f"""
            Topic: {prompt}
            Now create a plan for researching this topic both from the academic research and industry perspective, give me a solid plan.

            Return ONLY valid JSON. No explanations, no markdown, no extra text.
            Format EXACTLY:
            {{
            "plan": ["3-6 short bullet steps"],
            "tasks": [
                {{"task": "...", "tag": "research"}},
                {{"task": "...", "tag": "industry"}},
                {{"task": "...", "tag": "general"}}
            ]
            }}

            Rules:
            - tag must be exactly one of: "research", "industry", "general"
            - tasks should be parallelizable

            The example below is ONLY to show the level of detail and structure.
            Do NOT copy the example content.

            Example of a plan:
            1. Objective: Comprehensive history of the open web; Tim Berners-Lee's original 1989/1990 proposal; evolution to W3C and early web architecture; emergence of Web 1.0, Web 2.0, and the "open web" ethos.
            2. Core sources from W3C, CERN, reputable histories.
            3. Cover Semantic Web vision and standards (Linked Data, RDF, OWL, SPARQL, JSON-LD, schema.org).
            4. Then survey current trends where AIs/agents become primary web users: AI crawlers (GPTBot, Google-Extended, Common Crawl), content provenance (C2PA), structured data, APIs (OpenAPI, OAuth2/OIDC), pub/sub (WebSub), social federation (ActivityPub), data pods (Solid), identity (DID/VC).
            5. Look for forecasts and workshops (W3C, industry) on AI agents on the web, and implications for infrastructure, interfaces, and markets.
            6. Prioritize primary sources, official specs, and authoritative blogs; include recent (2023-2026) developments on AI crawlers, robots.txt and opt-outs for AI training, and privacy/ads shifts (Privacy Sandbox).

            Start with here is the plan and tasks
            """.strip()

        text = self.client.complete(system=system, user=user)

        try:
            data = json.loads(text)
            state["plan"] = data.get("plan", []) if isinstance(data.get("plan"), list) else []
            state["tasks"] = data.get("tasks", []) if isinstance(data.get("tasks"), list) else []
        except Exception:
            state["plan"] = [f"Research: {prompt}"]
            state["tasks"] = [
                {"task": f"Academic angle: {prompt}", "tag": "research"},
                {"task": f"Industry angle: {prompt}", "tag": "industry"},
                {"task": f"General overview: {prompt}", "tag": "general"},
            ]