import sys
import os
import json
import requests
import asyncio

from openai import OpenAI
from parallel import Parallel


MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

parallel_client = Parallel(
    api_key=os.environ["PARALLEL_API_KEY"],
    default_headers={"parallel-beta": "search-extract-2025-10-10"}
    )
client = OpenAI()
PARALLEL_BETAS = ["search-extract-2025-10-10"]


def init_state(prompt: str):
    return {
        "prompt": prompt,
        "plan": [],
        "tasks": [],
        "search_log": [],     # list of {agent, objective, urls}
        "evidence": [],       # list of {agent, url, excerpts}
    }


def planner_agent(state):
    prompt = state["prompt"]
    system = "You are a planner for a research agent."
    user = f"""
    Topic: {prompt}
    Now create a plan for researching this topic both from the academic research and industry perspective, give me a solid plan.
    
    Return ONLY valid JSON. No explanations, no markdown, no extra text.
    Format:
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

    resp = client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )

    text = (resp.output_text or "").strip()
    try:
        data = json.loads(text)
        state["plan"] = data.get("plan", []) if isinstance(data.get("plan"), list) else []
        state["tasks"] = data.get("tasks", []) if isinstance(data.get("tasks"), list) else []
    except Exception:
        state["plan"] = [f"Research: {prompt}"]
        state["tasks"] = [
            f"Academic angle: {prompt}",
            f"Industry angle: {prompt}",
            f"General overview: {prompt}",
        ]


def tool_search(objective: str, search_queries=None, max_results=10, max_chars_per_result=10):
    resp = parallel_client.beta.search(
        objective=objective,
        search_queries=search_queries or [],
        max_results=max_results,
        excerpts={"max_chars_per_result": max_chars_per_result},
    )
    return resp.results  # {url,title,publish_date,excerpts}


def tool_extract(urls, objective: str, max_chars_per_result=1000):
    resp = parallel_client.beta.extract(
        betas=PARALLEL_BETAS,
        urls=urls,
        objective=objective,
        excerpts={"max_chars_per_result": max_chars_per_result},
        full_content=False,
    )
    return resp.results  # {url,title,publish_date,excerpts}

def get_field(obj, name, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)

# todo: get max urls from config
def search_and_extract(task_text: str, agent_tag: str, main_prompt: str, max_urls=5):
    search_results = tool_search(objective=task_text, max_results=max_urls)
    urls = []
    for r in search_results:
        u = get_field(r, "url")
        if u: urls.append(u)
    urls = urls[:max_urls]
    log_item = {"agent": agent_tag, "objective": task_text, "urls": urls}
    if not urls:
        return log_item, []

    extract_results = tool_extract(urls=urls, objective=main_prompt)
    evidence = []
    for r in extract_results:
        url = get_field(r, "url")
        excerpts = get_field(r, "excerpts", []) or []
        for ex in excerpts:
            evidence.append({"agent": agent_tag, "url": url, "quote": ex})
    return log_item, evidence


def dedup_evidence(state): 
    seen = set()
    deduped = []
    for e in state["evidence"]:
        key = (e.get("url"), e.get("quote"))
        if key in seen: continue
        seen.add(key)
        deduped.append(e)
    state["evidence"] = deduped

async def run_exploration(state):
    prompt = state["prompt"]
    tasks = state.get("tasks", []) or []
    jobs = []
    for t in tasks:
        objective = t.get("task", "").strip()
        tag = t.get("tag", "general").strip()
        if not objective: continue
        jobs.append(
            asyncio.to_thread(search_and_extract, objective, tag, prompt)
        )
    results = await asyncio.gather(*jobs)

    for item in results:
        if not item: continue
        log_item, ev = item
        if log_item:
            state["search_log"].append(log_item)
        if ev:
            state["evidence"].extend(ev)
    dedup_evidence(state)


def summarizer_agent(state):
    prompt = state["prompt"]
    evidence = state.get("evidence", []) or []

    MAX_ITEMS = 80 #get from config
    MAX_CHARS = 18000 #get from config

    trimmed = []
    total = 0
    for e in evidence[:MAX_ITEMS]:
        item = {
            "agent": e.get("agent", ""),
            "url": e.get("url", ""),
            "quote": (e.get("quote", "") or "").strip()
        }
        s = json.dumps(item, ensure_ascii=False)
        if total + len(s) > MAX_CHARS: break
        trimmed.append(item)
        total += len(s)

    system = (
        "You are a careful research synthesizer.\n"
        "Use ONLY the provided evidence.\n"
        "Do not invent facts.\n"
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

    resp = client.responses.create(
        model=MODEL,
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


def markdown_agent(state):
    prompt = state["prompt"]
    summary = state.get("summary_structured", {}) or {}

    title = (summary.get("title") or prompt).strip()
    exec_sum = (summary.get("main_summary") or "").strip()
    insights = summary.get("key_insights") or []
    sections = summary.get("sections") or []
    tables = summary.get("tables") or []

    refs = summary.get("references") or []
    if not refs:
        seen = set()
        for e in (state.get("evidence", []) or []):
            u = e.get("url")
            if u and u not in seen:
                seen.add(u)
                refs.append(u)
        refs = refs[:40]

    def cite_urls(urls):
        urls = [u for u in (urls or []) if u]
        if not urls: return ""
        if len(urls) == 1: return f"(Source: {urls[0]})"
        return "(Sources: " + ", ".join(urls[:3]) + ")"

    md = []
    md.append(f"# {title}")
    md.append("")
    md.append("## Executive Summary")
    md.append("")
    md.append(exec_sum if exec_sum else "No executive summary available.")
    md.append("")

    # Key Strategic Insights block
    md.append("**Key Strategic Insights:**")
    md.append("")
    if insights:
        for it in insights[:8]:
            ins = (it.get("insight") or "").strip()
            src = cite_urls(it.get("sources"))
            if ins:
                md.append(f"* **{ins}** {src}".rstrip())
    else:
        md.append("* Evidence was insufficient to extract clear strategic insights.")
    md.append("")

    # Main sections
    for sec in sections[:12]:
        heading = (sec.get("heading") or "").strip()
        bullets = sec.get("bullets") or []
        if not heading:
            continue
        md.append(f"## {heading}")
        md.append("")
        if bullets:
            for b in bullets[:12]:
                pt = (b.get("point") or "").strip()
                src = cite_urls(b.get("sources"))
                if pt:
                    md.append(f"* {pt} {src}".rstrip())
        else:
            md.append("* (No extracted points.)")
        md.append("")

    # Tables
    for tb in tables[:6]:
        ttitle = (tb.get("title") or "").strip()
        cols = tb.get("columns") or []
        rows = tb.get("rows") or []
        src = cite_urls(tb.get("sources"))

        if ttitle:
            md.append(f"**Table: {ttitle}** {src}".rstrip())
            md.append("")
        if cols and rows:
            md.append("| " + " | ".join(cols) + " |")
            md.append("| " + " | ".join([":---"] * len(cols)) + " |")
            for r in rows[:12]:
                r = [("" if x is None else str(x)) for x in r]
                r = (r + [""] * len(cols))[:len(cols)]
                md.append("| " + " | ".join(r) + " |")
            md.append("")

    # References
    md.append("## References")
    md.append("")
    for i, u in enumerate(refs, 1):
        md.append(f"{i}. *Fetched web page*. {u}")

    state["final_report"] = "\n".join(md).strip()

async def run_controller(state):
    planner_agent(state)
    await run_exploration(state)
    summarizer_agent(state)
    markdown_agent(state)



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python main.py "your research prompt"')
        raise SystemExit(1)

    prompt = sys.argv[1].strip()
    state = init_state(prompt)

    # use cached state - remove this
    # with open('state.json', 'r') as file:
    #     data_dict = json.load(file)
    # state = data_dict

    asyncio.run(run_controller(state))

    ### cache state remove this
    # file_path = "state.json"
    # with open(file_path, "w") as json_file:
    #     json.dump(state, json_file, indent=4)

    print("Success")


# python3 main.py "tell me about the societal impact of AI"