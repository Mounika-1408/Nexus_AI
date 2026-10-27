import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginUser } from "../services/api";
import "../styles/login.css";

function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState(() => localStorage.getItem("nexusaiEmail") || "");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(() => Boolean(localStorage.getItem("nexusaiEmail")));
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await loginUser({ email, password });

      if (remember) {
        localStorage.setItem("nexusaiEmail", email);
      } else {
        localStorage.removeItem("nexusaiEmail");
      }

      navigate("/dashboard");
    } catch (err) {
      setError(err.message || "Failed to sign in. Please verify your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">

        <div className="logo-section">
          <div className="logo-icon">✦</div>
          <h1>
            Nexus<span>AI</span>
          </h1>
        </div>

        <h2>Welcome back</h2>
        <p className="subtitle">
          Sign in to continue to your analytics workspace
        </p>

        <form onSubmit={handleLogin}>
          <label htmlFor="email">Email address</label>
          <input
            id="email"
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              setError("");
            }}
            required
          />

          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              setError("");
            }}
            required
          />

          <div className="login-options">
            <label className="remember">
              <input
                type="checkbox"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
              />
              <span>Remember me</span>
            </label>

            <button
              type="button"
              className="forgot"
              onClick={() => alert("Please contact your administrator to reset your password.")}
            >
              Forgot password?
            </button>
          </div>

          {error && <div className="login-error" style={{ color: "#ef4444", marginTop: "8px", fontSize: "0.9rem" }}>{error}</div>}

          <button type="submit" className="signin-button" disabled={loading}>
            {loading ? "Signing in..." : <>Sign in <span>→</span></>}
          </button>
        </form>

        <div className="divider">
          <span></span>
          <p>OR</p>
          <span></span>
        </div>

        <button
          type="button"
          className="google-button"
          onClick={() => alert("Enterprise Google SSO is available for institutional deployments.")}
        >
          <strong>G</strong>
          <span>Continue with Google</span>
        </button>

        <p className="create-account">
          Don't have an account?{" "}
          <button
            type="button"
            onClick={() => navigate("/signup")}
          >
            Create account
          </button>
        </p>

        <p className="footer">
          © 2026 NexusAI · AI Powered Data Analytics
        </p>

      </div>
    </div>
  );
}

export default Login;