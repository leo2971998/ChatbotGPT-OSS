import React, { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import remarkGfm from "remark-gfm";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";

export default function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([
    {
      id: 0,
      type: "text",
      text: "Hello! Ask me for weather (e.g., \u201cweather in Houston\u201d).",
      sender: "bot",
      ts: Date.now(),
    },
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setError("");
    setInput("");

    const userMsg = {
      id: Date.now(),
      type: "text",
      text,
      sender: "user",
      ts: Date.now(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.error || "Request failed");

      if (data.reply) {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now() + 1,
            type: "text",
            text: String(data.reply ?? ""),
            sender: "bot",
            ts: Date.now(),
          },
        ]);
      }
      if (data.ui?.type === "weather") {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now() + 2,
            type: "card",
            sender: "bot",
            ts: Date.now(),
            card: data.ui,
          },
        ]);
      }
    } catch (e) {
      setError(e.message || "Something went wrong");
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 3,
          type: "text",
          text: "\u26a0\ufe0f " + (e.message || "Error"),
          sender: "bot",
          ts: Date.now(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () =>
    setMessages([
      {
        id: 0,
        type: "text",
        text: "New chat started. Ask me anything!",
        sender: "bot",
        ts: Date.now(),
      },
    ]);

  return (
    <div className="page">
      <div className="card">
        <header className="header">
          <div className="brand">
            <SparklesIcon />
            <span>Local Chat (Ollama)</span>
          </div>
          <div className="actions">
            <button className="btn ghost" onClick={clearChat} title="Clear chat">
              Clear
            </button>
          </div>
        </header>

        <main className="chat-window">
          {messages.map((m) =>
            m.type === "card" ? (
              <WeatherCard key={m.id} data={m.card} />
            ) : (
              <Message key={m.id} text={m.text} sender={m.sender} ts={m.ts} />
            )
          )}
          {loading && <Typing />}
          <div ref={endRef} />
        </main>

        <footer className="composer">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Type a message… (Enter to send, Shift+Enter for newline)"
            rows={1}
          />
          <button
            className="btn primary"
            onClick={handleSend}
            disabled={loading || !input.trim()}
          >
            {loading ? "Sending…" : "Send"}
          </button>
        </footer>

        {error && <div className="error">{error}</div>}

        <div className="meta">
          <span className="dot" />
          Backend: <code>{API_URL}</code>
        </div>
      </div>
    </div>
  );
}

function Message({ text, sender, ts }) {
  const isUser = sender === "user";
  return (
    <div className={`row ${isUser ? "right" : "left"}`}>
      {!isUser && <AvatarBot />}
      <div className={`bubble ${isUser ? "user" : "bot"}`}>
        <div className="content">
          <ReactMarkdown
            remarkPlugins={[remarkMath, remarkGfm]}
            rehypePlugins={[rehypeKatex]}
            components={{
              code({ inline, className, children, ...props }) {
                return inline ? (
                  <code className="inline-code" {...props}>
                    {children}
                  </code>
                ) : (
                  <pre className="code-block">
                    <code {...props}>{children}</code>
                  </pre>
                );
              },
            }}
          >
            {text}
          </ReactMarkdown>
        </div>
        <div className="timestamp">{new Date(ts).toLocaleTimeString()}</div>
      </div>
      {isUser && <AvatarUser />}
    </div>
  );
}

function Typing() {
  return (
    <div className="row left">
      <AvatarBot />
      <div className="bubble bot typing">
        <span className="dot1" />
        <span className="dot2" />
        <span className="dot3" />
      </div>
      <div className="wc-main">
        <div className="wc-temp">{Math.round(temperature)}°</div>
        <div className="wc-feels">Feels {Math.round(feelsLike)}°</div>
      </div>
      <div className="wc-right">
        <div>H:{Math.round(high)}° / L:{Math.round(low)}°</div>
        <div>Humidity: {Math.round(humidity)}%</div>
        <div>Wind: {Math.round(wind)} km/h</div>
        <div>UV: {uv ?? '—'}</div>
        <Legend />
      </div>
    </div>
  )
}

function Legend() {
  return (
    <div className="legend">
      <span className="chip good">Good</span>
      <span className="chip fair">Fair</span>
      <span className="chip poor">Poor</span>
    </div>
  );
}

function AvatarBot() {
  return (
    <div className="avatar bot">
      <SparklesIcon />
    </div>
  );
}

function AvatarUser() {
  return (
    <div className="avatar user">
      <UserIcon />
    </div>
  );
}

function SparklesIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" role="img" aria-label="bot">
      <path
        d="M5 3l1.5 4.5L11 9 6.5 10.5 5 15 3.5 10.5  -1 9 3.5 7.5 5 3zm10 3l2 6 6 2-6 2-2 6-2-6-6-2 6-2 2-6z"
        fill="currentColor"
      />
    </svg>
  );
}

function UserIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" role="img" aria-label="you">
      <path
        d="M12 12a5 5 0 100-10 5 5 0 000 10zm-8 9a8 8 0 1116 0v1H4v-1z"
        fill="currentColor"
      />
    </svg>
  );
}

function WeatherCard({ data }) {
  const {
    location,
    icon,
    condition,
    temperature,
    feelsLike,
    high,
    low,
    humidity,
    wind,
    uv,
  } = data || {};
  return (
    <div className="weather-card">
      <div className="wc-left">
        <div className="wc-icon">{icon || "\ud83c\udf21\ufe0f"}</div>
        <div>
          <div className="wc-location">{location}</div>
          <div className="wc-cond">{condition}</div>
        </div>
      </div>
      <div className="wc-main">
        <div className="wc-temp">{Math.round(temperature)}\u00b0</div>
        <div className="wc-feels">Feels {Math.round(feelsLike)}\u00b0</div>
      </div>
      <div className="wc-right">
        <div>H:{Math.round(high)}\u00b0 / L:{Math.round(low)}\u00b0</div>
        <div>Humidity: {Math.round(humidity)}%</div>
        <div>Wind: {Math.round(wind)} km/h</div>
        <div>UV: {uv ?? "\u2014"}</div>
        <Legend />
      </div>
    </div>
  );
}

function Legend() {
  return (
    <div className="legend">
      <span className="chip good">Good</span>
      <span className="chip fair">Fair</span>
      <span className="chip poor">Poor</span>
    </div>
  );
}

