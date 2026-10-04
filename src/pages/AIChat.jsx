import React, { useState } from "react";
import Sidebar from "../components/Sidebar";
import "../styles/AIChat.css";

function AIChat() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: "ai",
      text: "Hello! I'm NexusAI. I can help you understand your business data, find trends, and answer questions about your analytics.",
    },
  ]);

  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  const suggestions = [
    "What are my total sales?",
    "Which product performed best?",
    "Show me the sales trend",
    "What are the key insights?",
  ];

  const generateResponse = (question) => {
    const q = question.toLowerCase();

    if (q.includes("total sales") || q.includes("revenue")) {
      return "Based on your current dataset, total revenue is ₹15,20,000. Revenue has shown a positive trend compared with the previous period.";
    }

    if (q.includes("best") || q.includes("product")) {
      return "Product A is currently the top-performing product with revenue of ₹45,000, followed by Product B at ₹38,500.";
    }

    if (q.includes("trend")) {
      return "Your sales trend is generally increasing. Sales moved from ₹12,000 in January to ₹30,000 in June, indicating strong growth over the period.";
    }

    if (
      q.includes("insight") ||
      q.includes("insights") ||
      q.includes("analysis")
    ) {
      return "Here are the key insights: revenue is growing, Product A is the strongest performer, and June recorded the highest sales among the available months.";
    }

    if (q.includes("customer")) {
      return "Your current analytics indicate approximately 980 customers in the dataset.";
    }

    if (q.includes("order")) {
      return "The current dataset contains approximately 2,350 orders.";
    }

    return "I can help you analyze your dataset. Try asking about revenue, sales trends, products, customers, orders, or key business insights.";
  };

  const sendMessage = (messageText = input) => {
    const question = messageText.trim();

    if (!question || isTyping) {
      return;
    }

    const userMessage = {
      id: Date.now(),
      sender: "user",
      text: question,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);

    setTimeout(() => {
      const response = generateResponse(question);

      const aiMessage = {
        id: Date.now() + 1,
        sender: "ai",
        text: response,
      };

      setMessages((prev) => [...prev, aiMessage]);
      setIsTyping(false);
    }, 900);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage();
  };

  const clearChat = () => {
    setMessages([
      {
        id: Date.now(),
        sender: "ai",
        text: "Chat cleared. How can I help you analyze your data?",
      },
    ]);
  };

  return (
    <div className="ai-chat-page">

      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <main className="ai-chat-main">

        {/* Header */}
        <div className="ai-chat-header">

          <div className="ai-chat-title-section">

            <div className="ai-chat-icon">
              ✦
            </div>

            <div>
              <h1>NexusAI Assistant</h1>

              <p>
                Ask questions about your business data
              </p>
            </div>

          </div>

          <button
            className="clear-chat-button"
            onClick={clearChat}
          >
            Clear chat
          </button>

        </div>

        {/* Dataset Status */}
        <div className="dataset-status">

          <div className="dataset-status-left">
            <div className="dataset-icon">
              ◉
            </div>

            <div>
              <strong>Analytics dataset</strong>
              <span>Connected and ready for analysis</span>
            </div>
          </div>

          <div className="connected-status">
            <span></span>
            Connected
          </div>

        </div>

        {/* Chat Area */}
        <div className="chat-content">

          {messages.map((message) => (
            <div
              key={message.id}
              className={`message-row ${
                message.sender === "user"
                  ? "user-row"
                  : "ai-row"
              }`}
            >

              {/* AI Avatar */}
              {message.sender === "ai" && (
                <div className="message-avatar ai-avatar">
                  ✦
                </div>
              )}

              <div
                className={`message-bubble ${
                  message.sender === "user"
                    ? "user-message"
                    : "ai-message"
                }`}
              >
                {message.sender === "ai" && (
                  <div className="message-name">
                    NexusAI
                  </div>
                )}

                <p>{message.text}</p>
              </div>

              {/* User Avatar */}
              {message.sender === "user" && (
                <div className="message-avatar user-avatar">
                  U
                </div>
              )}

            </div>
          ))}

          {/* Typing */}
          {isTyping && (
            <div className="message-row ai-row">

              <div className="message-avatar ai-avatar">
                ✦
              </div>

              <div className="ai-message typing-message">

                <div className="message-name">
                  NexusAI
                </div>

                <div className="typing-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>

              </div>

            </div>
          )}

        </div>

        {/* Suggestions */}
        <div className="suggestions-section">

          <p>Try asking</p>

          <div className="suggestion-list">

            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => sendMessage(suggestion)}
                disabled={isTyping}
              >
                {suggestion}
              </button>
            ))}

          </div>

        </div>

        {/* Input */}
        <form
          className="chat-input-container"
          onSubmit={handleSubmit}
        >

          <input
            type="text"
            placeholder="Ask NexusAI anything about your data..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />

          <button
            type="submit"
            className="send-button"
            disabled={!input.trim() || isTyping}
          >
            →
          </button>

        </form>

        <p className="ai-disclaimer">
          NexusAI can make mistakes. Verify important business information.
        </p>

      </main>

    </div>
  );
}

export default AIChat;