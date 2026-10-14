import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2 } from "lucide-react";
import { mockChatWelcome } from "../mocks/mockChat";
import PropertyCard from "./PropertyCard";
import client from "../api/client";

export default function ChatWindow() {
  const [messages, setMessages] = useState([
    { role: "assistant", ...mockChatWelcome },
  ]);
  const [input, setInput] = useState("");
  const [propertyCache, setPropertyCache] = useState({});
  const [isStreaming, setIsStreaming] = useState(false);
  const eventSourceRef = useRef(null);
  const assistantMessageRef = useRef(null);

  const fetchPropertyDetails = async (ids) => {
    const idsToFetch = ids.filter((id) => !propertyCache[id]);
    if (idsToFetch.length === 0) return;
    
    const results = await Promise.allSettled(
      idsToFetch.map((id) => client.get(`/properties/${id}`))
    );
    setPropertyCache((prev) => {
      const updated = { ...prev };
      results.forEach((r, i) => {
        if (r.status === "fulfilled") {
          updated[idsToFetch[i]] = {
            ...r.value.data.property,
            images: r.value.data.images,
            amenities: r.value.data.amenities,
          };
        }
      });
      return updated;
    });
  };

  async function handleSend(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || isStreaming) return;

    const userMessage = { role: "user", response_text: text };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsStreaming(true);

    // Create placeholder for assistant message
    const tempId = Date.now();
    assistantMessageRef.current = {
      role: "assistant",
      response_text: "",
      referenced_property_ids: [],
      timing: {},
      tempId,
    };
    setMessages((prev) => [...prev, assistantMessageRef.current]);

    try {
      const response = await fetch("/api/v1/chat/message/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ message: text }),
      });

      if (!response.ok) {
        throw new Error("Stream failed");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullText = "";
      let done = false;

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split("\n");
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.chunk) {
                  fullText += data.chunk;
                  assistantMessageRef.current.response_text = fullText;
                  setMessages((prev) => prev.map((m) => (m.tempId === tempId ? { ...assistantMessageRef.current } : m)));
                }
                if (data.done) {
                  assistantMessageRef.current.referenced_property_ids = data.referenced_property_ids || [];
                  assistantMessageRef.current.timing = data.timing || {};
                  setMessages((prev) => prev.map((m) => (m.tempId === tempId ? { ...assistantMessageRef.current } : m)));
                  
                  if (data.referenced_property_ids?.length > 0) {
                    await fetchPropertyDetails(data.referenced_property_ids);
                  }
                }
              } catch (e) {
                // Ignore parse errors for incomplete chunks
              }
            }
          }
        }
      }
    } catch (err) {
      const errorMessage = {
        role: "assistant",
        response_text: err.response?.data?.detail || "Something went wrong. Please try again.",
        referenced_property_ids: [],
      };
      setMessages((prev) => prev.map((m) => (m.tempId === tempId ? errorMessage : m)));
    } finally {
      setIsStreaming(false);
    }
  }

  return (
    <div className="flex flex-col h-[500px] border border-gray-200 rounded-xl overflow-hidden bg-white">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={msg.tempId || i}
            className={`flex gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            {msg.role === "assistant" && (
              <div className="h-7 w-7 rounded-full bg-blue-100 flex items-center justify-center shrink-0">
                {msg.response_text === "" && isStreaming ? (
                  <Loader2 size={14} className="text-blue-600 animate-spin" />
                ) : (
                  <Bot size={14} className="text-blue-600" />
                )}
              </div>
            )}

            <div className="max-w-[75%] space-y-2">
              <div
                className={`px-3 py-2 rounded-2xl text-sm ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white rounded-br-sm"
                    : "bg-gray-100 text-gray-800 rounded-bl-sm"
                }`}
              >
                {msg.response_text}
                {isStreaming && msg.role === "assistant" && msg.response_text === "" && (
                  <span className="inline-block w-4 h-4 bg-current animate-pulse rounded ml-1" />
                )}
              </div>

              {msg.referenced_property_ids?.length > 0 && (
                <div className="grid grid-cols-1 gap-2">
                  {msg.referenced_property_ids.map((id) => {
                    const property = propertyCache[id];
                    if (!property) return null;
                    return <PropertyCard key={id} property={property} />;
                  })}
                </div>
              )}

              {msg.timing && Object.keys(msg.timing).length > 0 && (
                <div className="text-xs text-gray-400 flex gap-4">
                  <span>⚡ {msg.timing.total_ms || 0}ms total</span>
                  {msg.timing.extraction_ms && <span>🔍 {msg.timing.extraction_ms}ms extraction</span>}
                  {msg.timing.db_ms && <span>🗄️ {msg.timing.db_ms}ms DB</span>}
                  {msg.timing.rag_ms && <span>🤖 {msg.timing.rag_ms}ms RAG</span>}
                </div>
              )}
            </div>

            {msg.role === "user" && (
              <div className="h-7 w-7 rounded-full bg-gray-200 flex items-center justify-center shrink-0">
                <User size={14} className="text-gray-600" />
              </div>
            )}
          </div>
        ))}
      </div>

      <form
        onSubmit={handleSend}
        className="flex gap-2 border-t border-gray-100 p-3"
      >
        <label htmlFor="chat-message-input" className="sr-only">
          Type your message
        </label>
        <input
          id="chat-message-input"
          name="message"
          type="text"
          autoComplete="off"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about properties, budgets, or locations..."
          disabled={isStreaming}
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
        />
        <button
          type="submit"
          disabled={isStreaming || !input.trim()}
          className="h-9 w-9 rounded-lg bg-blue-600 text-white flex items-center justify-center hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isStreaming ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
        </button>
      </form>
    </div>
  );
}