"use client";

import { useEffect, useRef, useState } from "react";
import { Send, Wind, Loader2, Wrench } from "lucide-react";

type Msg = {
  role: "user" | "assistant";
  content: string;
  tools?: string[];
};

const SUGGESTIONS = [
  "What is a DAG in Airflow?",
  "How do I set up a task dependency?",
  "What's the difference between the scheduler and the executor?",
  "How do I run Airflow locally with the Astro CLI?",
];

export default function Home() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [threadId] = useState(() => `t_${Math.random().toString(36).slice(2)}`);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, loading]);

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: trimmed }]);
    setLoading(true);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: trimmed, threadId }),
      });
      const data = await res.json();
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: res.ok
            ? data.reply
            : `Error: ${data.error ?? "request failed"}`,
          tools: data.toolsUsed,
        },
      ]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: `Network error: ${String(e)}` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex h-[100dvh] max-w-3xl flex-col px-4">
      <header className="flex items-center gap-3 py-5">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-500/20 ring-1 ring-sky-400/40">
          <Wind className="h-5 w-5 text-sky-300" />
        </div>
        <div>
          <h1 className="text-lg font-semibold tracking-tight">
            Airflow Docs Copilot
          </h1>
          <p className="text-xs text-slate-400">
            Agentic RAG over Apache Airflow &amp; Astronomer docs + live web search
          </p>
        </div>
      </header>

      <div
        ref={scrollRef}
        className="flex-1 space-y-4 overflow-y-auto rounded-2xl bg-slate-900/40 p-4 ring-1 ring-white/5"
      >
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
            <p className="max-w-md text-sm text-slate-400">
              Ask anything about Airflow DAGs, operators, scheduling, or the
              Astro CLI. I retrieve from the docs first, then search the web when
              needed.
            </p>
            <div className="grid w-full max-w-lg grid-cols-1 gap-2 sm:grid-cols-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-left text-sm text-slate-300 transition hover:border-sky-400/40 hover:bg-sky-400/10"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div
            key={i}
            className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-sm ${
                m.role === "user"
                  ? "bg-sky-500 text-white"
                  : "bg-slate-800/80 text-slate-100 ring-1 ring-white/5"
              }`}
            >
              {m.content}
              {m.tools && m.tools.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5 border-t border-white/10 pt-2 text-[11px] text-slate-400">
                  <Wrench className="h-3 w-3" />
                  {m.tools.map((t) => (
                    <span
                      key={t}
                      className="rounded-full bg-white/5 px-2 py-0.5"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="flex items-center gap-2 rounded-2xl bg-slate-800/80 px-4 py-3 text-sm text-slate-300 ring-1 ring-white/5">
              <Loader2 className="h-4 w-4 animate-spin" /> Thinking…
            </div>
          </div>
        )}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
        className="my-4 flex items-center gap-2"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about Airflow…"
          className="flex-1 rounded-xl border border-white/10 bg-slate-900/60 px-4 py-3 text-sm outline-none placeholder:text-slate-500 focus:border-sky-400/50"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="flex h-11 w-11 items-center justify-center rounded-xl bg-sky-500 text-white transition hover:bg-sky-400 disabled:opacity-40"
        >
          <Send className="h-5 w-5" />
        </button>
      </form>
    </main>
  );
}
