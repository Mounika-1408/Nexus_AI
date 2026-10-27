import React, { useRef, useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import { sendChatMessage, fetchDatasets } from "../services/api";
import "../styles/VoiceAssistant.css";

function VoiceAssistant() {
  const [status, setStatus] = useState("Ready");
  const [transcript, setTranscript] = useState("");
  const [response, setResponse] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [isMuted, setIsMuted] = useState(false);
  const [datasets, setDatasets] = useState([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState("");
  const [browserSupported, setBrowserSupported] = useState(true);

  const recognitionRef = useRef(null);
  const transcriptRef = useRef("");
  const errorOccurredRef = useRef(false);

  useEffect(() => {
    // Check speech recognition support
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setBrowserSupported(false);
    }

    // Load available datasets
    fetchDatasets()
      .then((data) => {
        const list = Array.isArray(data) ? data : [];
        setDatasets(list);
        if (list.length > 0) {
          setSelectedDatasetId(list[0].id);
        }
      })
      .catch((err) => console.warn("Failed to load datasets for voice assistant:", err));

    return () => {
      // Cancel speech synthesis and stop recognition on unmount
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const speakText = (text) => {
    if (isMuted || !("speechSynthesis" in window)) return;
    try {
      window.speechSynthesis.cancel();
      const cleanText = text.replace(/[*_#`]/g, "");
      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      window.speechSynthesis.speak(utterance);
    } catch (e) {
      console.warn("Speech synthesis error:", e);
    }
  };

  const processQuery = async (question) => {
    if (!question || !question.trim()) {
      setStatus("Ready");
      return;
    }

    setStatus("Processing");
    setErrorMessage("");

    try {
      const chatRes = await sendChatMessage({
        message: question,
        dataset_id: selectedDatasetId ? parseInt(selectedDatasetId, 10) : null,
      });

      const answerText = chatRes.answer || "No response received from the analytical engine.";
      setResponse(answerText);
      setStatus("Responding");
      speakText(answerText);

      setTimeout(() => {
        setStatus("Ready");
      }, 1500);
    } catch (err) {
      console.error("Voice assistant query error:", err);
      const errDetail = err.message || "Failed to process query.";
      setErrorMessage(errDetail);
      setResponse(`Error: ${errDetail}`);
      setStatus("Ready");
    }
  };

  const startListening = () => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setErrorMessage("Speech recognition is not supported in this browser. Please use Chrome or Edge.");
      return;
    }

    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }

    setTranscript("");
    setResponse("");
    setErrorMessage("");
    transcriptRef.current = "";
    errorOccurredRef.current = false;
    setStatus("Listening");

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = "en-US";
      recognition.continuous = false;
      recognition.interimResults = true;

      recognition.onstart = () => {
        setStatus("Listening");
      };

      recognition.onresult = (event) => {
        let text = "";
        for (let i = 0; i < event.results.length; i++) {
          text += event.results[i][0].transcript;
        }
        transcriptRef.current = text;
        setTranscript(text);
      };

      recognition.onerror = (event) => {
        errorOccurredRef.current = true;
        let msg = "Microphone error. Please verify audio input.";
        if (event.error === "not-allowed") {
          msg = "Microphone permission denied. Please allow microphone access in your browser settings.";
        } else if (event.error === "no-speech") {
          msg = "No speech detected. Please press the mic and speak clearly.";
        } else if (event.error === "network") {
          msg = "Network connectivity error during voice recognition.";
        }
        setErrorMessage(msg);
        setStatus("Ready");
      };

      recognition.onend = () => {
        if (errorOccurredRef.current) {
          setStatus("Ready");
          return;
        }

        const captured = transcriptRef.current.trim();
        if (captured) {
          processQuery(captured);
        } else {
          setStatus("Ready");
        }
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      setErrorMessage("Could not initialize voice recognition.");
      setStatus("Ready");
    }
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
  };

  const handleSuggestion = (text) => {
    setTranscript(text);
    transcriptRef.current = text;
    processQuery(text);
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
                Talk naturally with NexusAI and receive live spoken analytics from your database.
              </p>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            {/* Dataset Selector */}
            {datasets.length > 0 && (
              <select
                value={selectedDatasetId}
                onChange={(e) => setSelectedDatasetId(e.target.value)}
                style={{
                  padding: "8px 12px",
                  borderRadius: "8px",
                  border: "1px solid #cbd5e1",
                  background: "#ffffff",
                  fontSize: "0.85rem",
                  color: "#334155"
                }}
              >
                {datasets.map((d) => (
                  <option key={d.id} value={d.id}>
                    Dataset #{d.id} ({d.file_name})
                  </option>
                ))}
              </select>
            )}

            {/* Mute / Unmute Toggle (V3 fix) */}
            <button
              onClick={() => {
                if (!isMuted && "speechSynthesis" in window) {
                  window.speechSynthesis.cancel();
                }
                setIsMuted(!isMuted);
              }}
              style={{
                padding: "8px 14px",
                borderRadius: "8px",
                border: "1px solid #cbd5e1",
                background: isMuted ? "#f1f5f9" : "#eff6ff",
                color: isMuted ? "#64748b" : "#2563eb",
                cursor: "pointer",
                fontWeight: "600",
                fontSize: "0.85rem"
              }}
            >
              {isMuted ? "🔇 Voice Muted" : "🔊 Audio On"}
            </button>

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
        </div>

        {/* Browser compatibility warning */}
        {!browserSupported && (
          <div style={{ background: "#fffbeb", border: "1px solid #fde68a", padding: "12px 16px", borderRadius: "10px", color: "#92400e", marginBottom: "16px" }}>
            ⚠️ Web Speech API is not supported in this browser. For voice input, please use Google Chrome or Microsoft Edge.
          </div>
        )}

        {/* Error notification */}
        {errorMessage && (
          <div style={{ background: "#fef2f2", border: "1px solid #fecaca", padding: "12px 16px", borderRadius: "10px", color: "#b91c1c", marginBottom: "16px" }}>
            {errorMessage}
          </div>
        )}

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
              onClick={status === "Listening" ? stopListening : startListening}
              aria-label="Toggle Microphone"
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
              ? "Querying database..."
              : status === "Responding"
              ? "NexusAI is speaking..."
              : "Click to start speaking"}
          </h2>

          <p className="voice-helper">
            {status === "Listening"
              ? "Speak naturally. We'll run the SQL query on completion."
              : "Ask anything about your business data"}
          </p>

          <button
            className={`start-button ${status === "Listening" ? "stop" : ""}`}
            onClick={status === "Listening" ? stopListening : startListening}
          >
            {status === "Listening" ? "⏹ Stop Listening" : "🎙 Start Speaking"}
          </button>

          {/* PROCESS STEPS */}
          <div className="voice-process">

            <div className={`process-item ${status === "Ready" ? "current" : ""}`}>
              <div className="process-icon">●</div>
              <span>Ready</span>
            </div>

            <div className="process-arrow">→</div>

            <div className={`process-item ${status === "Listening" ? "current" : ""}`}>
              <div className="process-icon">〽</div>
              <span>Listening</span>
            </div>

            <div className="process-arrow">→</div>

            <div className={`process-item ${status === "Processing" ? "current" : ""}`}>
              <div className="process-icon">⚙</div>
              <span>Processing</span>
            </div>

            <div className="process-arrow">→</div>

            <div className={`process-item ${status === "Responding" ? "current" : ""}`}>
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
                  <span>Speak clearly and ask about revenue, expenses, profit, or categories.</span>
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
              <h3>NexusAI Live Response</h3>
              <p>Calculated from verified database records</p>
            </div>
          </div>

          <div className="ai-response-area">

            <div className="ai-avatar">✦</div>

            <div>
              {response ? (
                <p>{response}</p>
              ) : (
                <>
                  <p>Your live response will appear here after you speak.</p>
                  <span>
                    Ask questions like "What is the total revenue?", "What are my total expenses?", or "Which category has the highest revenue?".
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

            <button onClick={() => handleSuggestion("What is the total revenue?")}>
              <span>▥</span>
              What is the total revenue?
            </button>

            <button onClick={() => handleSuggestion("Which category has the highest revenue?")}>
              <span>🏆</span>
              Which category has the highest revenue?
            </button>

            <button onClick={() => handleSuggestion("Which category has the lowest revenue?")}>
              <span>📉</span>
              Which category has the lowest revenue?
            </button>

            <button onClick={() => handleSuggestion("Summarize financial performance")}>
              <span>📊</span>
              Summarize financial performance
            </button>

          </div>

        </div>

        <p className="voice-disclaimer">
          ⓘ NexusAI voice assistant executes parameterized SQL queries against your uploaded records.
        </p>

      </main>
    </div>
  );
}

export default VoiceAssistant;