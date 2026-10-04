import { Routes, Route } from "react-router-dom";

import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import Upload from "./pages/Upload";
import Analytics from "./pages/Analytics";
import AIChat from "./pages/AIChat";
import Prediction from "./pages/Prediction";
import VoiceAssistant from "./pages/VoiceAssistant";
import Settings from "./pages/Settings";
function App() {
  return (
    <Routes>

      {/* Authentication */}
      <Route path="/" element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      {/* Main Application */}
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/upload" element={<Upload />} />
      <Route path="/analytics" element={<Analytics />} />
      <Route path="/chat" element={<AIChat />} />
      <Route path="/prediction" element={<Prediction />} />
      <Route path="/voice" element={<VoiceAssistant />} />
      <Route path="/settings" element={<Settings />} />

    </Routes>
  );
}

export default App;