import "../styles/Dashboard.css";

import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";
import KpiCard from "../components/KpiCard";
import PowerBIFrame from "../components/PowerBIFrame";
import RecentUploads from "../components/RecentUploads";
import AIInsights from "../components/AIInsights";

function Dashboard() {
  return (
    <div className="dashboard">

      {/* Fixed Sidebar */}
      <Sidebar />

      {/* Main Dashboard Area */}
      <div className="dashboard-content">

        {/* Navbar */}
        <Navbar />

        {/* Welcome Section */}
        <div className="dashboard-header">
          <h1>Welcome Back, Durga 👋</h1>

          <p>
            Here's today's business overview. Monitor your KPIs,
            analyze reports, and generate AI-powered insights.
          </p>
        </div>

        {/* KPI Cards */}
        <div className="kpi-container">

          <KpiCard
            title="Revenue"
            value="₹1,50,000"
            change="+12%"
          />

          <KpiCard
            title="Profit"
            value="₹45,000"
            change="+8%"
          />

          <KpiCard
            title="Orders"
            value="523"
            change="+15%"
          />

          <KpiCard
            title="Customers"
            value="210"
            change="+5%"
          />

        </div>

        {/* Power BI Section */}
        <PowerBIFrame />

        {/* Bottom Section */}
        <div className="bottom-section">

          <RecentUploads />

          <AIInsights />

        </div>

      </div>

    </div>
  );
}

export default Dashboard;