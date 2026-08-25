import { useEffect, useRef, useState, type SubmitEvent } from "react";
import { ApiError, sendChatMessage } from "../api/client";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  isError?: boolean;
}

function Chat() {
  const [conversationId] = useState(() => crypto.randomUUID());
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const scrollAnchorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isSending) return;

    setMessages((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role: "user", content: trimmed },
    ]);
    setInput("");
    setIsSending(true);

    try {
      const result = await sendChatMessage(conversationId, trimmed);
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: "assistant", content: result.answer },
      ]);
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.message
          : "Something went wrong. Please try again.";
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: message,
          isError: true,
        },
      ]);
    } finally {
      setIsSending(false);
    }
  }

  return (
    <section className="flex h-[28rem] flex-col rounded-2xl border border-slate-200 bg-white shadow-sm shadow-slate-200/60 dark:border-slate-800 dark:bg-slate-900 dark:shadow-none">
      <div className="border-b border-slate-200 p-6 pb-4 dark:border-slate-800">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
          Chat
        </h2>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Ask questions about the documents you've uploaded.
        </p>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto px-6 py-4">
        {messages.length === 0 ? (
          <p className="text-sm text-slate-400 dark:text-slate-600">
            No messages yet. Say hello.
          </p>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <p
                className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm whitespace-pre-wrap ${
                  message.role === "user"
                    ? "bg-indigo-600 text-white"
                    : message.isError
                      ? "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300"
                      : "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-100"
                }`}
              >
                {message.content}
              </p>
            </div>
          ))
        )}
        {isSending && (
          <div className="flex justify-start">
            <p className="max-w-[80%] rounded-2xl bg-slate-100 px-4 py-2 text-sm text-slate-400 dark:bg-slate-800 dark:text-slate-500">
              Thinking...
            </p>
          </div>
        )}
        <div ref={scrollAnchorRef} />
      </div>

      <form
        onSubmit={handleSubmit}
        className="flex gap-2 border-t border-slate-200 p-4 dark:border-slate-800"
      >
        <input
          type="text"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Type a message..."
          disabled={isSending}
          className="flex-1 rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm text-slate-900 outline-none placeholder:text-slate-400 focus:border-indigo-400 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-950/40 dark:text-slate-100 dark:focus:border-indigo-500"
        />
        <button
          type="submit"
          disabled={isSending || !input.trim()}
          className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60"
        >
          Send
        </button>
      </form>
    </section>
  );
}

export default Chat;
