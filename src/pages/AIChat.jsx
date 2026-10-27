import { useState, useEffect, useRef } from "react";
import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";
import { sendChatMessage, fetchDatasets } from "../services/api";

import "../styles/AIChat.css";

function AIChat() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: "ai",
      text: "Hello! I'm NexusAI Assistant. I can convert your natural language questions into safe SQL and answer queries about your business & financial data.",
    },
  ]);

  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [datasets, setDatasets] = useState([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState("");
  const chatBottomRef = useRef(null);

  const suggestions = [
    "What is the total revenue?",
    "Which category has the highest revenue?",
    "Which category has the lowest revenue?",
    "What is the average profit?",
    "Summarize financial performance",
    "How many records are available?",
  ];

  useEffect(() => {
    loadDatasetList();
  }, []);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  async function loadDatasetList() {
    try {
      const data = await fetchDatasets();
      const list = Array.isArray(data) ? data : [];
      setDatasets(list);
      if (list.length > 0 && !selectedDatasetId) {
        setSelectedDatasetId(list[0].id);
      }
    } catch (err) {
      console.error("Failed to load dataset list for chat:", err);
    }
  }

  async function sendMessage(messageText = input) {
    const question = messageText.trim();
    if (!question || isTyping) return;

    const userMsg = {
      id: Date.now(),
      sender: "user",
      text: question,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);

    try {
      const response = await sendChatMessage({
        message: question,
        dataset_id: selectedDatasetId || null,
      });

      const aiMsg = {
        id: Date.now() + 1,
        sender: "ai",
        text: response.answer,
        sql: response.sql,
        result: response.result,
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      const errorMsg = {
        id: Date.now() + 1,
        sender: "ai",
        text: `⚠️ Error: ${err.message || "Failed to process your request."}`,
        isError: true,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsTyping(false);
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage();
  };

  const clearChat = () => {
    setMessages([
      {
        id: Date.now(),
        sender: "ai",
        text: "Chat cleared. Ask me any question about your financial datasets!",
      },
    ]);
  };

  return (
    <div className="ai-chat-page" style={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar />

      <main className="ai-chat-main" style={{ flex: 1, padding: "24px", maxWidth: "1200px", margin: "0 auto", display: "flex", flexDirection: "column" }}>
        <Navbar />

        {/* Header */}
        <div className="ai-chat-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <div className="ai-chat-title-section" style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div className="ai-chat-icon" style={{ fontSize: "1.5rem", color: "#2563eb" }}>✦</div>
            <div>
              <h1 style={{ fontSize: "1.5rem", margin: 0, fontWeight: "700" }}>NexusAI Text-to-SQL Assistant</h1>
              <p style={{ color: "#64748b", margin: 0, fontSize: "0.875rem" }}>
                Ask questions in plain English. NexusAI generates safe SQL, queries PostgreSQL, and provides business answers.
              </p>
            </div>
          </div>

          <button
            className="clear-chat-button"
            onClick={clearChat}
            style={{ padding: "8px 16px", borderRadius: "8px", border: "1px solid #cbd5e1", background: "#ffffff", cursor: "pointer", fontSize: "0.875rem" }}
          >
            Clear chat
          </button>
        </div>

        {/* Dataset Selection Bar */}
        <div className="dataset-status" style={{ background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "10px", padding: "12px 16px", marginBottom: "20px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
          <div className="dataset-status-left" style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div className="dataset-icon" style={{ color: "#2563eb" }}>◉</div>
            <div>
              <strong style={{ fontSize: "0.9rem" }}>Select Dataset Scope: </strong>
              <select
                value={selectedDatasetId}
                onChange={(e) => setSelectedDatasetId(e.target.value)}
                style={{ padding: "4px 10px", borderRadius: "6px", border: "1px solid #cbd5e1", background: "#ffffff", marginLeft: "8px", fontSize: "0.875rem" }}
              >
                <option value="">All Uploaded Datasets (Global Aggregation)</option>
                {datasets.map((d) => (
                  <option key={d.id} value={d.id}>
                    Dataset #{d.id} - {d.file_name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="connected-status" style={{ color: "#16a34a", fontSize: "0.875rem", fontWeight: "600" }}>
            ● Text-to-SQL Engine Ready
          </div>
        </div>

        {/* Chat Area */}
        <div className="chat-content" style={{ flex: 1, overflowY: "auto", padding: "16px", background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "12px", minHeight: "380px", maxHeight: "550px", marginBottom: "20px" }}>
          {messages.map((message) => (
            <div
              key={message.id}
              className={`message-row ${message.sender === "user" ? "user-row" : "ai-row"}`}
              style={{ display: "flex", gap: "12px", marginBottom: "20px", justifyContent: message.sender === "user" ? "flex-end" : "flex-start" }}
            >
              {message.sender === "ai" && (
                <div className="message-avatar ai-avatar" style={{ width: "36px", height: "36px", borderRadius: "50%", background: "#eff6ff", color: "#2563eb", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: "bold" }}>
                  ✦
                </div>
              )}

              <div
                className={`message-bubble ${message.sender === "user" ? "user-message" : "ai-message"}`}
                style={{
                  maxWidth: "80%",
                  padding: "14px 18px",
                  borderRadius: "12px",
                  background: message.sender === "user" ? "#2563eb" : message.isError ? "#fef2f2" : "#f8fafc",
                  color: message.sender === "user" ? "#ffffff" : message.isError ? "#b91c1c" : "#0f172a",
                  border: message.sender === "user" ? "none" : message.isError ? "1px solid #fecaca" : "1px solid #e2e8f0"
                }}
              >
                {message.sender === "ai" && (
                  <div className="message-name" style={{ fontSize: "0.75rem", fontWeight: "700", color: "#64748b", marginBottom: "4px" }}>
                    NexusAI Assistant
                  </div>
                )}

                <p style={{ margin: 0, fontSize: "0.95rem", lineHeight: "1.5" }}>{message.text}</p>

                {/* Expandable Generated SQL */}
                {message.sql && (
                  <details style={{ marginTop: "12px", background: "#1e293b", color: "#f8fafc", borderRadius: "8px", padding: "10px", fontSize: "0.85rem" }}>
                    <summary style={{ cursor: "pointer", fontWeight: "600", color: "#60a5fa" }}>
                      🔍 View Generated SQL Query
                    </summary>
                    <pre style={{ margin: "8px 0 0 0", fontFamily: "monospace", overflowX: "auto", whiteSpace: "pre-wrap", color: "#38bdf8" }}>
                      {message.sql}
                    </pre>
                  </details>
                )}

                {/* Returned Database Results Table */}
                {message.result && message.result.length > 0 && (
                  <div style={{ marginTop: "12px", overflowX: "auto" }}>
                    <span style={{ fontSize: "0.75rem", fontWeight: "600", color: "#64748b", display: "block", marginBottom: "4px" }}>
                      Database Result Set:
                    </span>
                    <table style={{ width: "100%", fontSize: "0.8rem", borderCollapse: "collapse", background: "#ffffff", border: "1px solid #cbd5e1" }}>
                      <thead>
                        <tr style={{ background: "#f1f5f9" }}>
                          {Object.keys(message.result[0]).map((k) => (
                            <th key={k} style={{ padding: "6px 8px", border: "1px solid #cbd5e1", textTransform: "capitalize" }}>{k}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {message.result.map((row, idx) => (
                          <tr key={idx}>
                            {Object.values(row).map((v, i) => (
                              <td key={i} style={{ padding: "6px 8px", border: "1px solid #cbd5e1" }}>{String(v)}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {message.sender === "user" && (
                <div className="message-avatar user-avatar" style={{ width: "36px", height: "36px", borderRadius: "50%", background: "#2563eb", color: "#ffffff", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: "bold" }}>
                  U
                </div>
              )}
            </div>
          ))}

          {/* Typing Indicator */}
          {isTyping && (
            <div className="message-row ai-row" style={{ display: "flex", gap: "12px", marginBottom: "20px" }}>
              <div className="message-avatar ai-avatar" style={{ width: "36px", height: "36px", borderRadius: "50%", background: "#eff6ff", color: "#2563eb", display: "flex", alignItems: "center", justifyContent: "center" }}>
                ✦
              </div>
              <div className="ai-message typing-message" style={{ background: "#f8fafc", padding: "14px 18px", borderRadius: "12px", border: "1px solid #e2e8f0", color: "#64748b" }}>
                <span style={{ fontWeight: "500" }}>Analyzing your data & generating SQL...</span>
              </div>
            </div>
          )}

          <div ref={chatBottomRef} />
        </div>

        {/* Example Suggestions */}
        <div className="suggestions-section" style={{ marginBottom: "16px" }}>
          <p style={{ fontSize: "0.85rem", color: "#64748b", margin: "0 0 8px 0" }}>Suggested Questions:</p>
          <div className="suggestion-list" style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => sendMessage(suggestion)}
                disabled={isTyping}
                style={{
                  background: "#ffffff",
                  border: "1px solid #cbd5e1",
                  padding: "6px 12px",
                  borderRadius: "20px",
                  fontSize: "0.85rem",
                  cursor: isTyping ? "not-allowed" : "pointer",
                  color: "#334155"
                }}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>

        {/* Input Form */}
        <form className="chat-input-container" onSubmit={handleSubmit} style={{ display: "flex", gap: "10px" }}>
          <input
            type="text"
            placeholder="Ask a question (e.g. 'What is the total revenue?')..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isTyping}
            style={{ flex: 1, padding: "12px 16px", borderRadius: "8px", border: "1px solid #cbd5e1", fontSize: "0.95rem" }}
          />

          <button
            type="submit"
            className="send-button"
            disabled={!input.trim() || isTyping}
            style={{
              padding: "12px 24px",
              background: !input.trim() || isTyping ? "#94a3b8" : "#2563eb",
              color: "#ffffff",
              border: "none",
              borderRadius: "8px",
              fontWeight: "bold",
              cursor: !input.trim() || isTyping ? "not-allowed" : "pointer"
            }}
          >
            Send →
          </button>
        </form>

        <p className="ai-disclaimer" style={{ fontSize: "0.75rem", color: "#94a3b8", textAlign: "center", marginTop: "10px" }}>
          NexusAI uses strict SQL security validation. Only read-only SELECT queries are generated & executed.
        </p>
      </main>
    </div>
  );
}

export default AIChat;