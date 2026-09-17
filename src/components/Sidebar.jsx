import {
  FaChartPie,
  FaUpload,
  FaChartLine,
  FaRobot,
  FaBrain,
  FaMicrophone,
  FaCog,
  FaSignOutAlt
} from "react-icons/fa";

import { NavLink, useNavigate } from "react-router-dom";
import "../styles/Sidebar.css";

function Sidebar() {

  const navigate = useNavigate();

  return (

    <aside className="sidebar">

      {/* Logo */}
      <div className="logo">
        <h2>NexusAI</h2>
      </div>

      {/* Navigation */}
      <nav>

        <ul>

          <li>
            <NavLink
              to="/dashboard"
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              <FaChartPie className="icon" />
              <span>Dashboard</span>
            </NavLink>
          </li>

          <li>
            <NavLink
              to="/upload"
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              <FaUpload className="icon" />
              <span>Upload Dataset</span>
            </NavLink>
          </li>

          <li>
            <NavLink
              to="/analytics"
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              <FaChartLine className="icon" />
              <span>Analytics</span>
            </NavLink>
          </li>

          <li>
            <NavLink
              to="/chat"
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              <FaRobot className="icon" />
              <span>AI Chat</span>
            </NavLink>
          </li>

          <li>
            <NavLink
              to="/prediction"
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              <FaBrain className="icon" />
              <span>Prediction</span>
            </NavLink>
          </li>

          <li>
            <NavLink
              to="/voice"
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              <FaMicrophone className="icon" />
              <span>Voice Assistant</span>
            </NavLink>
          </li>

          <li>
            <NavLink
              to="/settings"
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              <FaCog className="icon" />
              <span>Settings</span>
            </NavLink>
          </li>

        </ul>

      </nav>

      {/* Logout */}
      <div
        className="logout"
        onClick={() => navigate("/")}
      >
        <FaSignOutAlt className="icon" />
        <span>Logout</span>
      </div>

    </aside>

  );
}

export default Sidebar;