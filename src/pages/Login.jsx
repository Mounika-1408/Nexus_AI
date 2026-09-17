import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/login.css";

function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = (e) => {
    e.preventDefault();

    setError("");

    // Get the account created on the Signup page
    const savedUser = localStorage.getItem("nexusaiUser");

    if (!savedUser) {
      setError("No account found. Please create an account first.");
      return;
    }

    const user = JSON.parse(savedUser);

    // Check email and password
    if (email === user.email && password === user.password) {
      
      // Remember user if checkbox is selected
      if (remember) {
        localStorage.setItem("nexusaiEmail", email);
      } else {
        localStorage.removeItem("nexusaiEmail");
      }

      // Save login status
      localStorage.setItem("nexusaiLoggedIn", "true");

      // Go to Dashboard
      navigate("/dashboard");
    } else {
      setError("Invalid email or password.");
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

            <button type="button" className="forgot">
              Forgot password?
            </button>
          </div>

          {error && <div className="login-error">{error}</div>}

          <button type="submit" className="signin-button">
            Sign in <span>→</span>
          </button>
        </form>

        <div className="divider">
          <span></span>
          <p>OR</p>
          <span></span>
        </div>

        <button type="button" className="google-button">
          <strong>G</strong>
          <span>Continue with Google</span>
        </button>

        <p className="create-account">
          Don't have an account?

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