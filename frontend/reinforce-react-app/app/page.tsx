"use client";

import { useState } from "react";
import remarkGfm from "remark-gfm";
import ReactMarkdown from "react-markdown";

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [md, setMd] = useState("");

  async function run() {
    setLoading(true);
    setMd("");
    const r = await fetch("/api/research", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });
    const data = await r.json();
    setMd(data.markdown || data.error || "No response");
    setLoading(false);
  }

  return (
    <div className="mx-auto max-w-3xl p-6">
      <h1 className="text-2xl font-semibold">Deep Research</h1>

      <div className="mt-4 flex gap-2">
        <input
          className="flex-1 rounded border px-3 py-2"
          placeholder="Enter your research question..."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && run()}
        />
        <button
          className="rounded bg-black px-4 py-2 text-white disabled:opacity-50"
          disabled={!prompt.trim() || loading}
          onClick={run}
        >
          {loading ? "Running..." : "Start"}
        </button>
      </div>

      <div className="mt-6">
          {md ? (
            <div className="markdown-body rounded-lg border bg-white p-6">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{md}</ReactMarkdown>
            </div>
          ) : null}
      </div>
    </div>
  );
}



