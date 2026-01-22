from core.config import Settings


class MarkdownAgent:
    def __init__(self, settings: Settings):
        self.settings = settings

    def run(self, state: dict):
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
            if not urls:
                return ""
            if len(urls) == 1:
                return f"(Source: {urls[0]})"
            return "(Sources: " + ", ".join(urls[:3]) + ")"

        md = []
        md.append(f"# {title}")
        md.append("")
        md.append("## Executive Summary")
        md.append("")
        md.append(exec_sum if exec_sum else "No executive summary available.")
        md.append("")

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

        md.append("## References")
        md.append("")
        for i, u in enumerate(refs, 1):
            md.append(f"{i}. *Fetched web page*. {u}")

        state["final_report"] = "\n".join(md).strip()