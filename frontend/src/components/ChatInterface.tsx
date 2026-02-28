import { useState, useRef, useEffect } from "react";

interface Message {
  role: "user" | "bot";
  text: string;
}

const styles: Record<string, React.CSSProperties> = {
  wrapper: {
    display: "flex",
    flexDirection: "column" as const,
    height: "100%",
  },
  messages: {
    flex: 1,
    overflowY: "auto" as const,
    padding: "1rem",
    display: "flex",
    flexDirection: "column" as const,
    gap: "0.75rem",
  },
  bubble: (role: "user" | "bot") => ({
    maxWidth: "70%",
    padding: "0.65rem 1rem",
    borderRadius: role === "user" ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
    background: role === "user" ? "#2563eb" : "#fff",
    color: role === "user" ? "#fff" : "#111",
    alignSelf: role === "user" ? "flex-end" : "flex-start",
    boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
    whiteSpace: "pre-wrap" as const,
    lineHeight: 1.5,
  }),
  form: {
    display: "flex",
    gap: "0.5rem",
    padding: "0.75rem 1rem",
    borderTop: "1px solid #eee",
    background: "#fff",
  },
  input: {
    flex: 1,
    padding: "0.6rem 0.9rem",
    border: "1px solid #ddd",
    borderRadius: 24,
    fontSize: "1rem",
    outline: "none",
  },
  sendBtn: {
    padding: "0.6rem 1.2rem",
    background: "#2563eb",
    color: "#fff",
    border: "none",
    borderRadius: 24,
    fontWeight: 600,
    cursor: "pointer",
    fontSize: "0.95rem",
  },
  thinking: {
    color: "#999",
    fontSize: "0.85rem",
    alignSelf: "flex-start" as const,
    padding: "0.4rem 0.8rem",
  },
};

export default function ChatInterface({ userId }: { userId: string }) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "bot",
      text: "Hello! Ask me anything about your family tree. You can write in Polish, Czech or English.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setMessages((prev) => [...prev, { role: "user", text }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, userId }),
      });
      const data = await res.json();
      const reply = res.ok ? data.reply : data.detail ?? "Error processing your request.";
      setMessages((prev) => [...prev, { role: "bot", text: reply }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: "Network error. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.wrapper}>
      <div style={styles.messages}>
        {messages.map((msg, i) => (
          <div key={i} style={styles.bubble(msg.role)}>
            {msg.text}
          </div>
        ))}
        {loading && <div style={styles.thinking}>Thinking…</div>}
        <div ref={bottomRef} />
      </div>
      <form style={styles.form} onSubmit={handleSend}>
        <input
          style={styles.input}
          type="text"
          placeholder="Ask about your family…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
          autoFocus
        />
        <button style={styles.sendBtn} type="submit" disabled={loading}>
          Send
        </button>
      </form>
    </div>
  );
}
