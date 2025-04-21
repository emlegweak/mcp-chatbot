import { useEffect, useState } from "react";
import { fetchStreamedResponse } from "../api/chat";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export default function ChatBot() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const el = document.getElementById("chat-scroll");
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    // add user message
    setMessages((prev) => [...prev, { role: "user", content: input }]);
    setInput("");
    setIsLoading(true);

    let assistantMessage = ""; // track the growing assistant message

    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);
    const assistantIndex = messages.length + 1; // index where assistant will be appended

    await fetchStreamedResponse(input, (chunk) => {
      assistantMessage += chunk;

      setMessages((prev) => {
        const updated = [...prev];
        // only update the last assistant message
        updated[assistantIndex] = {
          role: "assistant",
          content: assistantMessage,
        };
        return updated;
      });
    });

    setIsLoading(false);
  };

  return (
    <div className="max-w-2xl mx-auto p-4">
      <div
        id="chat-scroll"
        className="bg-white border rounded-md p-4 h-96 overflow-y-auto mb-4"
      >
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex mb-4 ${
              msg.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-xs px-4 py-2 rounded-lg shadow ${
                msg.role === "user"
                  ? "bg-primary-subtle text-black self-end"
                  : "bg-secondary-subtle text-gray-800 self-start"
              }`}
            >
              <div className="text-xs mb-1">
                {msg.role === "user" ? "You" : "Assistant"}
              </div>
              <p className="whitespace-pre-wrap">{msg.content || ""}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="flex gap-2 items-end">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className={`flex-1 p-2 border rounded-md transition-opacity ${
            isLoading ? "opacity-25" : ""
          }`}
          placeholder="Ask something..."
          rows={2}
        />
        <button
          onClick={handleSend}
          className={`ml-2 px-4 py-2 rounded-md transition-opacity ${
            isLoading ? "btn-primary cursor-not-allowed" : "btn-secondary"
          } text-white`}
          disabled={isLoading}
        >
          {isLoading ? "Thinking..." : "Send"}
        </button>
      </div>
    </div>
  );
}
