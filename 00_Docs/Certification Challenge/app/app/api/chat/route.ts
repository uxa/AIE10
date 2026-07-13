import { NextRequest, NextResponse } from "next/server";
import { HumanMessage } from "@langchain/core/messages";
import { buildAgent } from "@/lib/agent";

export const runtime = "nodejs";
export const maxDuration = 60;

// Reuse the compiled agent across warm invocations.
let agentPromise: ReturnType<typeof buildAgent> | null = null;
function getAgent() {
  if (!agentPromise) agentPromise = buildAgent();
  return agentPromise;
}

export async function POST(req: NextRequest) {
  try {
    if (!process.env.OPENAI_API_KEY) {
      return NextResponse.json(
        { error: "OPENAI_API_KEY is not configured on the server." },
        { status: 500 },
      );
    }

    const { message, threadId } = await req.json();
    if (!message || typeof message !== "string") {
      return NextResponse.json(
        { error: "`message` (string) is required." },
        { status: 400 },
      );
    }

    const agent = await getAgent();
    const result = await agent.invoke(
      { messages: [new HumanMessage(message)] },
      // thread_id drives the LangGraph memory checkpointer (multi-turn memory).
      { configurable: { thread_id: threadId || "default" } },
    );

    const messages = result.messages;
    const last = messages[messages.length - 1];
    const toolsUsed = (messages as Array<{ tool_calls?: { name: string }[] }>)
      .flatMap((m) => m.tool_calls ?? [])
      .map((t) => t.name);

    return NextResponse.json({
      reply:
        typeof last.content === "string"
          ? last.content
          : JSON.stringify(last.content),
      toolsUsed: Array.from(new Set(toolsUsed)),
    });
  } catch (err) {
    console.error("/api/chat error", err);
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Unknown error" },
      { status: 500 },
    );
  }
}
