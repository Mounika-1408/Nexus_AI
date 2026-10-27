import { useState, useEffect } from "react";
import "../styles/Dashboard.css";

import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";
import KpiCard from "../components/KpiCard";
import RecentUploads from "../components/RecentUploads";
import AIInsights from "../components/AIInsights";

import {
  fetchDatasets,
  fetchDatasetMetadata,
  fetchDatasetSummary,
} from "../services/api";

function Dashboard() {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [selectedDatasetId, setSelectedDatasetId] = useState(null);
  const [selectedMetadata, setSelectedMetadata] = useState(null);
  const [selectedSummary, setSelectedSummary] = useState(null);
  const [detailsLoading, setDetailsLoading] = useState(false);

  const [kpiData, setKpiData] = useState({
    totalDatasets: 0,
    totalRecords: 0,
    etlStatus: "Active",
    avgQualityScore: "0%",
  });

  useEffect(() => {
    loadDashboardData();
  }, []);

  async function loadDashboardData() {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchDatasets();
      setDatasets(data);

      if (data && data.length > 0) {
        setSelectedDatasetId(data[0].id);
        fetchDetailsForDataset(data[0].id);

        // Fetch metadata in parallel to compute actual quality score and total records
        const metaResults = await Promise.all(
          data.map((ds) => fetchDatasetMetadata(ds.id).catch(() => null))
        );

        let totalRecs = 0;
        let qualitySum = 0;
        let qualityCount = 0;

        for (const meta of metaResults) {
          if (meta) {
            if (typeof meta.total_rows === "number") totalRecs += meta.total_rows;
            if (typeof meta.data_quality_score === "number") {
              qualitySum += meta.data_quality_score;
              qualityCount++;
            }
          }
        }

        const anyProcessing = data.some((d) => d.status === "processing");
        const anyFailed = data.some((d) => d.status === "failed");
        const realStatus = anyProcessing ? "Processing" : anyFailed ? "Warning" : "Active";
        const avgScore = qualityCount > 0 ? (qualitySum / qualityCount).toFixed(1) + "%" : "N/A";

        setKpiData({
          totalDatasets: data.length,
          totalRecords: totalRecs,
          etlStatus: realStatus,
          avgQualityScore: avgScore,
        });
      } else {
        setKpiData({
          totalDatasets: 0,
          totalRecords: 0,
          etlStatus: "Idle",
          avgQualityScore: "N/A",
        });
      }
    } catch (err) {
      setError("Failed to load dashboard metrics from backend: " + err.message);
    } finally {
      setLoading(false);
    }
  }

  async function fetchDetailsForDataset(datasetId) {
    try {
      setDetailsLoading(true);
      const [meta, summary] = await Promise.all([
        fetchDatasetMetadata(datasetId).catch(() => null),
        fetchDatasetSummary(datasetId).catch(() => null),
      ]);
      setSelectedMetadata(meta);
      setSelectedSummary(summary);
    } catch (err) {
      console.error("Error fetching dataset details:", err);
    } finally {
      setDetailsLoading(false);
    }
  }

  const selectedDataset = datasets.find((d) => d.id === selectedDatasetId);

  return (
    <div className="dashboard">
      <Sidebar />

      <div className="dashboard-content">
        <Navbar />

        <div className="dashboard-header">
          <h1>Enterprise AI Data Overview 👋</h1>
          <p>
            Monitor real-time business KPIs, dataset ETL processing, data quality scores, and AI analytics.
          </p>
        </div>

        {error && <div className="error-banner" style={{ padding: "12px", background: "#fee2e2", color: "#b91c1c", borderRadius: "8px", marginBottom: "16px" }}>{error}</div>}

        {/* KPI Cards */}
        <div className="kpi-container">
          <KpiCard
            title="Total Datasets"
            value={loading ? "..." : String(kpiData.totalDatasets)}
            change="Real Backend Count"
          />
          <KpiCard
            title="Total Records"
            value={loading ? "..." : kpiData.totalRecords.toLocaleString()}
            change="Cleaned & Ingested"
          />
          <KpiCard
            title="ETL Status"
            value={kpiData.etlStatus}
            change="Automated Pipeline"
          />
          <KpiCard
            title="Data Quality Score"
            value={kpiData.avgQualityScore}
            change="Automated Assessment"
          />
        </div>

        {/* Dataset Selection & Details View */}
        {datasets.length > 0 && (
          <div className="dataset-details-card" style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "12px", padding: "20px", marginBottom: "24px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "12px" }}>
              <div>
                <h2 style={{ fontSize: "1.25rem", fontWeight: "600", color: "#1e293b" }}>Dataset Metadata & ETL Details</h2>
                <p style={{ fontSize: "0.875rem", color: "#64748b" }}>Select a dataset to view automated cleaning results, metadata, and financial summary</p>
              </div>

              <select
                value={selectedDatasetId || ""}
                onChange={(e) => {
                  const id = parseInt(e.target.value, 10);
                  setSelectedDatasetId(id);
                  fetchDetailsForDataset(id);
                }}
                style={{ padding: "8px 12px", borderRadius: "8px", border: "1px solid #cbd5e1", background: "#f8fafc", fontWeight: "500" }}
              >
                {datasets.map((d) => (
                  <option key={d.id} value={d.id}>
                    Dataset #{d.id} - {d.file_name} ({d.file_type.toUpperCase()})
                  </option>
                ))}
              </select>
            </div>

            {detailsLoading ? (
              <p style={{ color: "#64748b" }}>Loading metadata for selected dataset...</p>
            ) : selectedDataset ? (
              <div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "16px", marginBottom: "16px" }}>
                  <div style={{ background: "#f8fafc", padding: "12px", borderRadius: "8px" }}>
                    <span style={{ fontSize: "0.75rem", color: "#64748b", display: "block" }}>File Name</span>
                    <strong style={{ color: "#0f172a" }}>{selectedDataset.file_name}</strong>
                  </div>
                  <div style={{ background: "#f8fafc", padding: "12px", borderRadius: "8px" }}>
                    <span style={{ fontSize: "0.75rem", color: "#64748b", display: "block" }}>File Type</span>
                    <strong style={{ color: "#0f172a" }}>{selectedDataset.file_type.toUpperCase()}</strong>
                  </div>
                  <div style={{ background: "#f8fafc", padding: "12px", borderRadius: "8px" }}>
                    <span style={{ fontSize: "0.75rem", color: "#64748b", display: "block" }}>Processing Status</span>
                    <strong style={{ color: "#16a34a" }}>{selectedDataset.status}</strong>
                  </div>
                  <div style={{ background: "#f8fafc", padding: "12px", borderRadius: "8px" }}>
                    <span style={{ fontSize: "0.75rem", color: "#64748b", display: "block" }}>Total Rows</span>
                    <strong style={{ color: "#0f172a" }}>{selectedMetadata ? selectedMetadata.total_rows : "N/A"}</strong>
                  </div>
                  <div style={{ background: "#f8fafc", padding: "12px", borderRadius: "8px" }}>
                    <span style={{ fontSize: "0.75rem", color: "#64748b", display: "block" }}>Cleaned Rows</span>
                    <strong style={{ color: "#0f172a" }}>{selectedMetadata ? selectedMetadata.cleaned_rows : "N/A"}</strong>
                  </div>
                  <div style={{ background: "#f8fafc", padding: "12px", borderRadius: "8px" }}>
                    <span style={{ fontSize: "0.75rem", color: "#64748b", display: "block" }}>Duplicates Removed</span>
                    <strong style={{ color: "#0f172a" }}>{selectedMetadata ? selectedMetadata.duplicates_removed : 0}</strong>
                  </div>
                  <div style={{ background: "#f8fafc", padding: "12px", borderRadius: "8px" }}>
                    <span style={{ fontSize: "0.75rem", color: "#64748b", display: "block" }}>Data Quality Score</span>
                    <strong style={{ color: "#2563eb" }}>{selectedMetadata ? `${selectedMetadata.data_quality_score}%` : "N/A"}</strong>
                  </div>
                </div>

                {selectedSummary && (
                  <div style={{ background: "#eff6ff", border: "1px solid #bfdbfe", padding: "14px", borderRadius: "8px", marginTop: "12px" }}>
                    <h4 style={{ margin: "0 0 8px 0", color: "#1e40af", fontSize: "0.95rem" }}>Dataset Financial Summary Metrics</h4>
                    <div style={{ display: "flex", gap: "24px", flexWrap: "wrap", fontSize: "0.875rem", color: "#1e3a8a" }}>
                      <span><strong>Total Revenue:</strong> ${selectedSummary.total_revenue ? selectedSummary.total_revenue.toLocaleString() : 0}</span>
                      <span><strong>Total Expenses:</strong> ${selectedSummary.total_expenses ? selectedSummary.total_expenses.toLocaleString() : 0}</span>
                      <span><strong>Total Profit:</strong> ${selectedSummary.total_profit ? selectedSummary.total_profit.toLocaleString() : 0}</span>
                      <span><strong>Records Count:</strong> {selectedSummary.total_records || 0}</span>
                    </div>
                  </div>
                )}
              </div>
            ) : null}
          </div>
        )}

        {/* Bottom Section */}
        <div className="bottom-section">
          <RecentUploads datasets={datasets} loading={loading} />
          <AIInsights summary={selectedSummary} metadata={selectedMetadata} />
        </div>
      </div>
    </div>
  );
}

export default Dashboard;