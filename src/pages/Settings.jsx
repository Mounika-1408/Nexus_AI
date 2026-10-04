import React, { useState } from "react";
import Sidebar from "../components/Sidebar";
import "../styles/Settings.css";

function Settings() {
  const [name, setName] = useState("Durga Bhavani");
  const [email, setEmail] = useState("admin@nexusai.com");

  const [editingName, setEditingName] = useState(false);

  const [changingEmail, setChangingEmail] = useState(false);
  const [newEmail, setNewEmail] = useState("");
  const [verificationCode, setVerificationCode] = useState("");

  const [codeSent, setCodeSent] = useState(false);
  const [message, setMessage] = useState("");

  const [emailNotifications, setEmailNotifications] = useState(true);
  const [aiNotifications, setAiNotifications] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  /* =========================
     SAVE NAME
  ========================= */

  const saveName = () => {
    if (!name.trim()) {
      setMessage("Name cannot be empty.");
      return;
    }

    setEditingName(false);
    setMessage("Name updated successfully.");

    setTimeout(() => {
      setMessage("");
    }, 2500);
  };

  /* =========================
     SEND EMAIL VERIFICATION
  ========================= */

  const sendVerificationCode = async () => {
    if (!newEmail.trim()) {
      setMessage("Please enter a new email address.");
      return;
    }

    try {
      /*
        Backend API will send the actual code.

        Example:
        POST /api/settings/request-email-change

        Body:
        {
          "newEmail": "newmail@gmail.com"
        }
      */

      const response = await fetch(
        "http://localhost:5000/api/settings/request-email-change",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            newEmail: newEmail,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        setMessage(data.message || "Unable to send verification code.");
        return;
      }

      setCodeSent(true);
      setMessage("Verification code sent to your new email.");
    } catch (error) {
      console.error(error);

      setMessage(
        "Email service is not connected yet. Backend integration is required."
      );
    }
  };

  /* =========================
     VERIFY EMAIL CODE
  ========================= */

  const verifyEmail = async () => {
    if (!verificationCode.trim()) {
      setMessage("Please enter the verification code.");
      return;
    }

    try {
      /*
        Backend API will verify the code.

        Example:
        POST /api/settings/verify-email-change

        Body:
        {
          "newEmail": "newmail@gmail.com",
          "code": "123456"
        }
      */

      const response = await fetch(
        "http://localhost:5000/api/settings/verify-email-change",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            newEmail: newEmail,
            code: verificationCode,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        setMessage(data.message || "Invalid verification code.");
        return;
      }

      setEmail(newEmail);

      setChangingEmail(false);
      setCodeSent(false);
      setNewEmail("");
      setVerificationCode("");

      setMessage("Email address changed successfully.");

      setTimeout(() => {
        setMessage("");
      }, 3000);
    } catch (error) {
      console.error(error);

      setMessage(
        "Email verification service is not connected yet."
      );
    }
  };

  /* =========================
     SAVE SETTINGS
  ========================= */

  const handleSave = () => {
    localStorage.setItem(
      "nexusaiSettings",
      JSON.stringify({
        name,
        email,
        emailNotifications,
        aiNotifications,
        autoRefresh,
      })
    );

    setMessage("Settings saved successfully.");

    setTimeout(() => {
      setMessage("");
    }, 2500);
  };

  /* =========================
     LOGOUT
  ========================= */

  const handleLogout = () => {
    localStorage.removeItem("nexusaiLoggedInUser");
    window.location.href = "/";
  };

  return (
    <div className="settings-page">
      <Sidebar />

      <main className="settings-main">

        {/* HEADER */}

        <div className="settings-header">
          <div>
            <h1>Settings</h1>
            <p>
              Manage your NexusAI account and application preferences.
            </p>
          </div>
        </div>

        {/* ================= PROFILE ================= */}

        <div className="settings-card">

          <div className="settings-card-header">

            <div className="settings-icon profile-icon">
              👤
            </div>

            <div>
              <h2>Profile</h2>
              <p>Manage your account information</p>
            </div>

          </div>

          <div className="profile-section">

            <div className="profile-avatar">
              {name.charAt(0).toUpperCase()}
            </div>

            <div className="profile-info">

              {/* NAME */}

              <div className="profile-edit-row">

                <div className="form-group">

                  <label>Full Name</label>

                  <input
                    type="text"
                    value={name}
                    disabled={!editingName}
                    onChange={(e) => setName(e.target.value)}
                  />

                </div>

                {!editingName ? (
                  <button
                    className="edit-button"
                    onClick={() => setEditingName(true)}
                  >
                    Edit
                  </button>
                ) : (
                  <button
                    className="save-small-button"
                    onClick={saveName}
                  >
                    Save
                  </button>
                )}

              </div>

              {/* EMAIL */}

              <div className="profile-edit-row email-row">

                <div className="form-group">

                  <label>Email Address</label>

                  <input
                    type="email"
                    value={email}
                    disabled
                  />

                </div>

                <button
                  className="edit-button"
                  onClick={() => {
                    setChangingEmail(true);
                    setMessage("");
                  }}
                >
                  Change Email
                </button>

              </div>

            </div>

          </div>

          {/* EMAIL CHANGE BOX */}

          {changingEmail && (
            <div className="email-change-box">

              <div className="email-change-header">

                <div>
                  <h3>Change Email Address</h3>

                  <p>
                    A verification code will be sent to your new
                    email address.
                  </p>
                </div>

                <button
                  className="close-button"
                  onClick={() => {
                    setChangingEmail(false);
                    setCodeSent(false);
                    setNewEmail("");
                    setVerificationCode("");
                  }}
                >
                  ×
                </button>

              </div>

              {!codeSent ? (
                <>
                  <div className="form-group">

                    <label>New Email Address</label>

                    <input
                      type="email"
                      placeholder="Enter your new email"
                      value={newEmail}
                      onChange={(e) =>
                        setNewEmail(e.target.value)
                      }
                    />

                  </div>

                  <button
                    className="send-code-button"
                    onClick={sendVerificationCode}
                  >
                    Send Verification Code
                  </button>
                </>
              ) : (
                <>
                  <div className="verification-message">
                    📧 Verification code sent to
                    <strong> {newEmail}</strong>
                  </div>

                  <div className="form-group">

                    <label>Verification Code</label>

                    <input
                      type="text"
                      maxLength="6"
                      placeholder="Enter 6-digit code"
                      value={verificationCode}
                      onChange={(e) =>
                        setVerificationCode(
                          e.target.value.replace(/\D/g, "")
                        )
                      }
                    />

                  </div>

                  <button
                    className="send-code-button"
                    onClick={verifyEmail}
                  >
                    Verify & Change Email
                  </button>

                  <button
                    className="resend-button"
                    onClick={sendVerificationCode}
                  >
                    Resend Code
                  </button>
                </>
              )}

            </div>
          )}

          {/* MESSAGE */}

          {message && (
            <div className="settings-message">
              {message}
            </div>
          )}

        </div>

        {/* ================= NOTIFICATIONS ================= */}

        <div className="settings-card">

          <div className="settings-card-header">

            <div className="settings-icon notification-icon">
              🔔
            </div>

            <div>
              <h2>Notifications</h2>
              <p>
                Choose which notifications you want to receive
              </p>
            </div>

          </div>

          <div className="setting-option">

            <div>
              <h3>Email Notifications</h3>
              <p>
                Receive important updates and reports by email.
              </p>
            </div>

            <button
              className={`toggle ${
                emailNotifications ? "active" : ""
              }`}
              onClick={() =>
                setEmailNotifications(!emailNotifications)
              }
            >
              <span></span>
            </button>

          </div>

          <div className="setting-option">

            <div>
              <h3>AI Insights</h3>
              <p>
                Receive notifications when new AI-powered insights
                are available.
              </p>
            </div>

            <button
              className={`toggle ${
                aiNotifications ? "active" : ""
              }`}
              onClick={() =>
                setAiNotifications(!aiNotifications)
              }
            >
              <span></span>
            </button>

          </div>

        </div>

        {/* ================= DATA ================= */}

        <div className="settings-card">

          <div className="settings-card-header">

            <div className="settings-icon data-icon">
              📊
            </div>

            <div>
              <h2>Data Preferences</h2>
              <p>
                Configure how NexusAI handles your analytics data
              </p>
            </div>

          </div>

          <div className="setting-option">

            <div>
              <h3>Automatic Data Refresh</h3>
              <p>
                Automatically refresh analytics when new data
                is available.
              </p>
            </div>

            <button
              className={`toggle ${
                autoRefresh ? "active" : ""
              }`}
              onClick={() =>
                setAutoRefresh(!autoRefresh)
              }
            >
              <span></span>
            </button>

          </div>

        </div>

        {/* ================= SECURITY ================= */}

        <div className="settings-card">

          <div className="settings-card-header">

            <div className="settings-icon security-icon">
              🔒
            </div>

            <div>
              <h2>Security</h2>
              <p>Manage your account security</p>
            </div>

          </div>

          <div className="security-actions">

            <button
              className="secondary-button"
              onClick={() =>
                alert(
                  "Password change functionality will be connected to the backend."
                )
              }
            >
              Change Password
            </button>

            <button
              className="logout-button"
              onClick={handleLogout}
            >
              Logout
            </button>

          </div>

        </div>

        {/* SAVE */}

        <div className="settings-footer">

          <button
            className="save-button"
            onClick={handleSave}
          >
            Save Changes
          </button>

        </div>

      </main>
    </div>
  );
}

export default Settings;