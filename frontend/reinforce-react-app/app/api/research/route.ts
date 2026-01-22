import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const { prompt } = await req.json();

  const r = await fetch("http://localhost:8000/research", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });

  if (!r.ok) {
    const txt = await r.text();
    return NextResponse.json({ error: txt }, { status: 500 });
  }

  const data = await r.json();
  return NextResponse.json({ markdown: data.final_report });
}