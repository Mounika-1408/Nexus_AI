import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { registerUser } from "../services/api";
import "../styles/Signup.css";

function Signup() {
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSignup = async (e) => {
    e.preventDefault();
    setError("");

    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      await registerUser({
        name: name.trim(),
        email: email.trim(),
        password
      });

      navigate("/dashboard");
    } catch (err) {
      setError(err.message || "Failed to create account. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="signup-page">
      <div className="signup-container">

        {/* Logo */}
        <div className="signup-logo-section">
          <div className="signup-logo-icon">✦</div>
          <h1>
            Nexus<span>AI</span>
          </h1>
        </div>

        {/* Heading */}
        <h2>Create your account</h2>
        <p className="signup-subtitle">
          Get started with your AI-powered analytics workspace
        </p>

        {/* Form */}
        <form onSubmit={handleSignup}>
          <label htmlFor="name">Full name</label>
          <input
            id="name"
            type="text"
            placeholder="Enter your full name"
            value={name}
            onChange={(e) => {
              setName(e.target.value);
              setError("");
            }}
            required
          />

          <label htmlFor="signup-email">Email address</label>
          <input
            id="signup-email"
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              setError("");
            }}
            required
          />

          <label htmlFor="signup-password">Password</label>
          <input
            id="signup-password"
            type="password"
            placeholder="Create a password"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              setError("");
            }}
            required
          />

          <label htmlFor="confirm-password">Confirm password</label>
          <input
            id="confirm-password"
            type="password"
            placeholder="Confirm your password"
            value={confirmPassword}
            onChange={(e) => {
              setConfirmPassword(e.target.value);
              setError("");
            }}
            required
          />

          {error && (
            <div className="signup-error" style={{ color: "#ef4444", marginTop: "8px", fontSize: "0.9rem" }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            className="signup-button"
            disabled={loading}
          >
            {loading ? "Creating account..." : <>Create account <span>→</span></>}
          </button>
        </form>

        <p className="already-account">
          Already have an account?{" "}
          <button
            type="button"
            onClick={() => navigate("/")}
          >
            Sign in
          </button>
        </p>

        <p className="signup-footer">
          © 2026 NexusAI · AI Powered Data Analytics
        </p>

      </div>
    </div>
  );
}

export default Signup;