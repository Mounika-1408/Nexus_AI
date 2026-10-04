import React, { useRef, useState } from "react";
import Sidebar from "../components/Sidebar";
import "../styles/VoiceAssistant.css";

function VoiceAssistant() {
  const [status, setStatus] = useState("Ready");
  const [transcript, setTranscript] = useState("");
  const [response, setResponse] = useState("");

  const recognitionRef = useRef(null);

  const startListening = () => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert(
        "Speech recognition is not supported in this browser. Please use Google Chrome."
      );
      return;
    }

    setTranscript("");
    setResponse("");
    setStatus("Listening");

    const recognition = new SpeechRecognition();

    recognition.lang = "en-IN";
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onstart = () => {
      setStatus("Listening");
    };

    recognition.onresult = (event) => {
      let text = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        text += event.results[i][0].transcript;
      }

      setTranscript(text);
    };

    recognition.onerror = (event) => {
      console.log("Speech recognition error:", event.error);
      setStatus("Ready");
    };

    recognition.onend = () => {
      setStatus("Processing");

      setTimeout(() => {
        setStatus("Responding");

        // Temporary demo AI response
        // Later replace this with your friend's backend API.
        generateResponse(transcript);

        setTimeout(() => {
          setStatus("Ready");
        }, 1200);
      }, 700);
    };

    recognitionRef.current = recognition;
    recognition.start();
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
  };

  const generateResponse = (question) => {
    const q = question.toLowerCase();

    if (q.includes("sales") || q.includes("revenue")) {
      setResponse(
        "Your current total revenue is ₹15,20,000. Revenue has shown a positive trend compared with the previous period."
      );
    } else if (q.includes("product") || q.includes("best")) {
      setResponse(
        "Product A is currently the top-performing product with revenue of ₹45,000, followed by Product B at ₹38,500."
      );
    } else if (q.includes("trend")) {
      setResponse(
        "Your sales trend is generally increasing. Sales moved from ₹12,000 in January to ₹30,000 in June."
      );
    } else if (q.includes("customer")) {
      setResponse(
        "Your current analytics indicate approximately 980 customers."
      );
    } else if (q.includes("order")) {
      setResponse(
        "The current dataset contains approximately 2,350 orders."
      );
    } else if (q.trim() !== "") {
      setResponse(
        "I received your question. Once the NexusAI AI backend is connected, I can provide a complete AI-powered analysis."
      );
    }
  };

  const handleSuggestion = (text) => {
    setTranscript(text);
    setStatus("Processing");

    setTimeout(() => {
      setStatus("Responding");
      generateResponse(text);

      setTimeout(() => {
        setStatus("Ready");
      }, 1000);
    }, 500);
  };

  return (
    <div className="voice-page">
      <Sidebar />

      <main className="voice-main">

        {/* HEADER */}
        <div className="voice-header">
          <div className="voice-title-wrapper">
            <div className="header-mic-icon">🎙</div>

            <div>
              <h1>Voice Assistant</h1>
              <p>
                Talk naturally with NexusAI and get instant insights from your
                data.
              </p>
            </div>
          </div>

          <div className="voice-status">
            <span className={`status-dot ${status.toLowerCase()}`}></span>
            {status}

            <div className="status-waves">
              <span></span>
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>

        {/* MAIN VOICE CONSOLE */}
        <div className="voice-console">

          <div className="voice-animation">

            <div className="sound-wave left-wave">
              <span></span>
              <span></span>
              <span></span>
              <span></span>
              <span></span>
              <span></span>
              <span></span>
            </div>

            <button
              className={`main-mic ${status === "Listening" ? "active" : ""}`}
              onClick={
                status === "Listening"
                  ? stopListening
                  : startListening
              }
            >
              🎙
            </button>

            <div className="sound-wave right-wave">
              <span></span>
              <span></span>
              <span></span>
              <span></span>
              <span></span>
              <span></span>
              <span></span>
            </div>

          </div>

          <h2>
            {status === "Listening"
              ? "Listening..."
              : status === "Processing"
              ? "Processing..."
              : status === "Responding"
              ? "NexusAI is responding..."
              : "Click to start speaking"}
          </h2>

          <p className="voice-helper">
            {status === "Listening"
              ? "Speak naturally. Take your time."
              : "Ask anything about your business data"}
          </p>

          <button
            className={`start-button ${
              status === "Listening" ? "stop" : ""
            }`}
            onClick={
              status === "Listening"
                ? stopListening
                : startListening
            }
          >
            {status === "Listening"
              ? "⏹ Stop Listening"
              : "🎙 Start Speaking"}
          </button>

          {/* PROCESS STEPS */}
          <div className="voice-process">

            <div
              className={`process-item ${
                status === "Ready" ? "current" : ""
              }`}
            >
              <div className="process-icon">●</div>
              <span>Ready</span>
            </div>

            <div className="process-arrow">→</div>

            <div
              className={`process-item ${
                status === "Listening" ? "current" : ""
              }`}
            >
              <div className="process-icon">〽</div>
              <span>Listening</span>
            </div>

            <div className="process-arrow">→</div>

            <div
              className={`process-item ${
                status === "Processing" ? "current" : ""
              }`}
            >
              <div className="process-icon">⚙</div>
              <span>Processing</span>
            </div>

            <div className="process-arrow">→</div>

            <div
              className={`process-item ${
                status === "Responding" ? "current" : ""
              }`}
            >
              <div className="process-icon">✦</div>
              <span>Responding</span>
            </div>

          </div>
        </div>

        {/* TRANSCRIPT */}
        <div className="voice-card">

          <div className="card-heading">
            <div className="card-heading-icon">〽</div>

            <div>
              <h3>Live Transcript</h3>
              <p>Your spoken question appears here</p>
            </div>
          </div>

          <div className="transcript-area">
            <div className="small-mic">🎙</div>

            <div>
              {transcript ? (
                <p className="transcript-text">{transcript}</p>
              ) : (
                <>
                  <p>Your speech will appear here...</p>
                  <span>Speak clearly and take your time.</span>
                </>
              )}
            </div>
          </div>

        </div>

        {/* AI RESPONSE */}
        <div className="voice-card response-card">

          <div className="card-heading">
            <div className="ai-card-icon">✦</div>

            <div>
              <h3>NexusAI Response</h3>
              <p>AI-generated insights from your business data</p>
            </div>
          </div>

          <div className="ai-response-area">

            <div className="ai-avatar">✦</div>

            <div>
              {response ? (
                <p>{response}</p>
              ) : (
                <>
                  <p>Your AI response will appear here after you speak.</p>
                  <span>
                    Ask anything about your data — sales, revenue, products,
                    customers, trends and more.
                  </span>
                </>
              )}
            </div>

          </div>

        </div>

        {/* SUGGESTIONS */}
        <div className="voice-card suggestions-card">

          <div className="suggestion-heading">
            <span>✦</span>
            <h3>Try asking</h3>
          </div>

          <div className="suggestion-grid">

            <button
              onClick={() =>
                handleSuggestion("What are my total sales?")
              }
            >
              <span>▥</span>
              What are my total sales?
            </button>

            <button
              onClick={() =>
                handleSuggestion("Which product performed best?")
              }
            >
              <span>🏆</span>
              Which product performed best?
            </button>

            <button
              onClick={() =>
                handleSuggestion("Show me the sales trend")
              }
            >
              <span>↗</span>
              Show me the sales trend
            </button>

            <button
              onClick={() =>
                handleSuggestion("Give me key business insights")
              }
            >
              <span>💡</span>
              Give me key business insights
            </button>

          </div>

        </div>

        <p className="voice-disclaimer">
          ⓘ NexusAI can make mistakes. Verify important business information.
        </p>

      </main>
    </div>
  );
}

export default VoiceAssistant;