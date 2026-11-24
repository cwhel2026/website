"use client";

import { useState } from "react";
import { apiPost } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

type ChatResponse = {
  conversation_id: string;
  reply: string;
  provider: string;
};

export default function AssistantPage() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<{ role: string; text: string }[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function send() {
    if (!input.trim()) return;
    const token = getToken();
    if (!token) return;
    setLoading(true);
    setMessages((m) => [...m, { role: "user", text: input }]);
    const prompt = input;
    setInput("");
    try {
      const res = await apiPost<ChatResponse>("/api/v1/assistant/chat", {
        message: prompt,
        conversation_id: conversationId,
      }, token);
      setConversationId(res.conversation_id);
      setMessages((m) => [...m, { role: "assistant", text: res.reply }]);
    } catch {
      setMessages((m) => [...m, { role: "assistant", text: "Assistant unavailable." }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-[70vh] flex-col">
      <h1 className="text-2xl font-semibold text-emerald-950">AI Assistant</h1>
      <p className="text-sm text-slate-600">
        Answers use live backend tools only ({`provider: deterministic_tools`}). No fabricated jobs or revenue.
      </p>
      <div className="mt-4 flex-1 overflow-y-auto rounded-lg border bg-slate-50 p-4 text-sm">
        {messages.length === 0 && (
          <p className="text-slate-500">Try: &quot;What jobs have I got tomorrow?&quot; or &quot;Which driveways need painting?&quot;</p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`mb-3 ${m.role === "user" ? "text-right" : ""}`}>
            <span
              className={`inline-block rounded-lg px-3 py-2 ${
                m.role === "user" ? "bg-emerald-900 text-white" : "bg-white border"
              }`}
            >
              {m.text}
            </span>
          </div>
        ))}
      </div>
      <div className="mt-3 flex gap-2">
        <input
          className="flex-1 rounded-lg border px-3 py-2 text-sm"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Ask about schedule, weather risk, approvals…"
        />
        <button
          type="button"
          disabled={loading}
          onClick={send}
          className="rounded-full bg-emerald-900 px-5 py-2 text-sm text-white disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}