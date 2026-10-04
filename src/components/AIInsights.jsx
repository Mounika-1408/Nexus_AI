import "../styles/Analytics.css";
import Sidebar from "../components/Sidebar";

function Analytics() {
  return (
    <div className="analytics-page">

      <Sidebar />

      <div style={{ marginLeft: "274px", padding: "40px" }}>
        <h1>Analytics Page</h1>
        <p>Sidebar + Analytics are working.</p>
      </div>

    </div>
  );
}

export default Analytics;