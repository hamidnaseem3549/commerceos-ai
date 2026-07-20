"use client";

import { useState, useRef, useEffect } from "react";
import { chat, chat as chatApi, getAgents } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  agent?: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Hi! I'm the CommerceOS AI Assistant. Ask me about orders, inventory, fraud detection, pricing, or anything about the store!", agent: "System" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [agents, setAgents] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [threadId] = useState(() => Math.random().toString(36).slice(2, 10));

  useEffect(() => {
    getAgents().then(({ agents }) => setAgents(agents)).catch(() => {});
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const examples = [
    "Where is my order O2001?",
    "Do we have white t-shirts in stock?",
    "Check order O2004 for fraud",
    "Any items on sale?",
    "Cancel order O2005",
  ];

  const sendMessage = async (query: string) => {
    if (!query.trim() || loading) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setLoading(true);

    try {
      const result = await chatApi(query, threadId);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: result.answer, agent: result.agent },
      ]);
    } catch (e: any) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${e.message}`, agent: "System" },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const agentColors: Record<string, string> = {
    support: "from-blue-500 to-blue-600",
    inventory: "from-yellow-500 to-orange-500",
    fraud: "from-red-500 to-red-600",
    order: "from-purple-500 to-purple-600",
    pricing: "from-green-500 to-emerald-500",
  };

  const getAgentColor = (name: string) => {
    const key = Object.keys(agentColors).find((k) => name.toLowerCase().includes(k));
    return key ? agentColors[key] : "from-gray-500 to-gray-600";
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-dark-100">🤖 AI Assistant</h1>
        <p className="text-gray-500 mt-1">
          Routed by <span className="font-semibold">LangGraph Supervisor</span> —{" "}
          {agents.length} agents available
        </p>
      </div>

      {/* Example buttons */}
      <div className="flex gap-2 flex-wrap mb-6">
        {examples.map((ex) => (
          <button
            key={ex}
            onClick={() => sendMessage(ex)}
            className="px-4 py-2 bg-white rounded-xl text-sm text-gray-600 hover:bg-gray-50
                       border border-gray-200 hover:border-brand-300 transition-all shadow-sm"
          >
            {ex}
          </button>
        ))}
      </div>

      {/* Chat messages */}
      <div className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="h-[500px] overflow-y-auto p-6 space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} animate-slide-up`}>
              <div
                className={`max-w-[80%] rounded-2xl p-4 ${
                  msg.role === "user"
                    ? "bg-gradient-to-r from-dark-100 to-dark-200 text-white rounded-br-sm"
                    : "bg-gray-50 text-gray-800 rounded-bl-sm"
                }`}
              >
                {msg.agent && msg.role === "assistant" && (
                  <span className={`inline-block text-xs font-bold px-2 py-0.5 rounded-full text-white mb-2 bg-gradient-to-r ${getAgentColor(msg.agent)}`}>
                    {msg.agent}
                  </span>
                )}
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start animate-fade-in">
              <div className="bg-gray-50 rounded-2xl rounded-bl-sm p-4">
                <div className="flex gap-1.5">
                  <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t p-4">
          <form
            onSubmit={(e) => { e.preventDefault(); sendMessage(input); }}
            className="flex gap-3"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about orders, inventory, fraud, or pricing..."
              className="input-field flex-1"
              disabled={loading}
            />
            <button type="submit" disabled={loading || !input.trim()} className="btn-primary">
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
