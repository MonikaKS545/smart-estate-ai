import { useState } from "react";
import { Send, Bot, User } from "lucide-react";
import { getMockChatResponse, mockChatWelcome } from "../mocks/mockChat";
import PropertyCard from "./PropertyCard";
import mockProperties from "../mocks/mockProperties";

/**
 * Reusable chat window. Uses getMockChatResponse() from mockChat.js —
 * swapping this for a real POST /chat/message call later is a
 * one-line change (see the handleSend function below).
 */
export default function ChatWindow() {
  const [messages, setMessages] = useState([
    { role: "assistant", ...mockChatWelcome },
  ]);
  const [input, setInput] = useState("");

  function handleSend(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text) return;

    const userMessage = { role: "user", response_text: text };

    // This is the one call to swap for a real API request later:
    // const reply = await axios.post('/chat/message', { message: text })
    const reply = getMockChatResponse(text);
    const assistantMessage = { role: "assistant", ...reply };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setInput("");
  }

  return (
    <div className="flex flex-col h-[500px] border border-gray-200 rounded-xl overflow-hidden bg-white">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex gap-2 ${
              msg.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            {msg.role === "assistant" && (
              <div className="h-7 w-7 rounded-full bg-blue-100 flex items-center justify-center shrink-0">
                <Bot size={14} className="text-blue-600" />
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
              </div>

              {msg.referenced_property_ids?.length > 0 && (
                <div className="grid grid-cols-1 gap-2">
                  {msg.referenced_property_ids.map((id) => {
                    const property = mockProperties.find((p) => p.id === id);
                    if (!property) return null;
                    return <PropertyCard key={id} property={property} />;
                  })}
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
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          className="h-9 w-9 rounded-lg bg-blue-600 text-white flex items-center justify-center hover:bg-blue-700"
        >
          <Send size={16} />
        </button>
      </form>
    </div>
  );
}