"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";

import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { ThreadListSidebar } from "@/components/assistant-ui/threadlist-sidebar";
import { Separator } from "@/components/ui/separator";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";

export const Assistant = () => {
  const [prompt, setPrompt] = useState("");
  const [markdown, setMarkdown] = useState("");
  const [loading, setLoading] = useState(false);

  async function run() {
    const p = prompt.trim();
    if (!p) return;

    setLoading(true);
    setMarkdown("");

    const r = await fetch("/api/research", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: p }),
    });

    const data = await r.json();
    setMarkdown(data?.markdown || data?.error || "No output");
    setLoading(false);
  }

  return (
    <SidebarProvider>
      <div className="flex h-dvh w-full pr-0.5">
        {/* optional: remove this if you want even simpler UI */}
        <ThreadListSidebar />

        <SidebarInset>
          <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
            <SidebarTrigger />
            <Separator orientation="vertical" className="mr-2 h-4" />
            <Breadcrumb>
              <BreadcrumbList>
                <BreadcrumbItem className="hidden md:block">
                  <BreadcrumbLink
                    href="https://www.assistant-ui.com/docs/getting-started"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Research Agent UI
                  </BreadcrumbLink>
                </BreadcrumbItem>
                <BreadcrumbSeparator className="hidden md:block" />
                <BreadcrumbItem>
                  <BreadcrumbPage>One-shot</BreadcrumbPage>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>
          </header>

          <div className="flex h-[calc(100dvh-4rem)] flex-col overflow-hidden">
            {/* Input */}
            <div className="border-b p-4">
              <div className="mx-auto flex max-w-3xl gap-2">
                <input
                  className="w-full rounded-md border px-3 py-2"
                  placeholder="Enter research question…"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      run();
                    }
                  }}
                />
                <button
                  className="rounded-md bg-black px-4 py-2 text-white disabled:opacity-50"
                  onClick={run}
                  disabled={loading || !prompt.trim()}
                >
                  {loading ? "Running…" : "Search"}
                </button>
              </div>
            </div>

            {/* Output */}
            <div className="flex-1 overflow-auto p-6">
              <div className="prose mx-auto max-w-3xl">
                {markdown ? (
                  <ReactMarkdown>{markdown}</ReactMarkdown>
                ) : (
                  <p className="text-muted-foreground">
                    Output will appear here.
                  </p>
                )}
              </div>
            </div>
          </div>
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
};