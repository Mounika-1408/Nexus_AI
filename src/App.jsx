import { Routes, Route, Navigate } from "react-router-dom";

import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import Upload from "./pages/Upload";
import Analytics from "./pages/Analytics";
import AIChat from "./pages/AIChat";
import Prediction from "./pages/Prediction";
import VoiceAssistant from "./pages/VoiceAssistant";
import Settings from "./pages/Settings";

function ProtectedRoute({ children }) {
  const token = localStorage.getItem("nexusaiToken");
  if (!token) {
    return <Navigate to="/" replace />;
  }
  return children;
}

function PublicRoute({ children }) {
  const token = localStorage.getItem("nexusaiToken");
  if (token) {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
}

function App() {
  return (
    <Routes>

      {/* Public Authentication Routes */}
      <Route
        path="/"
        element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        }
      />
      <Route
        path="/signup"
        element={
          <PublicRoute>
            <Signup />
          </PublicRoute>
        }
      />

      {/* Protected Application Routes */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/upload"
        element={
          <ProtectedRoute>
            <Upload />
          </ProtectedRoute>
        }
      />
      <Route
        path="/analytics"
        element={
          <ProtectedRoute>
            <Analytics />
          </ProtectedRoute>
        }
      />
      <Route
        path="/chat"
        element={
          <ProtectedRoute>
            <AIChat />
          </ProtectedRoute>
        }
      />
      <Route
        path="/prediction"
        element={
          <ProtectedRoute>
            <Prediction />
          </ProtectedRoute>
        }
      />
      <Route
        path="/voice"
        element={
          <ProtectedRoute>
            <VoiceAssistant />
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <Settings />
          </ProtectedRoute>
        }
      />

      {/* Catch-all redirect */}
      <Route path="*" element={<Navigate to="/" replace />} />

    </Routes>
  );
}

export default App;