import { useState, useEffect, useMemo } from "react";
import { Link } from "react-router-dom";
import {
  TrendingUp,
  Tv,
  Calendar,
  Layers,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Database,
  RefreshCw,
  Info,
  ShieldCheck,
  FileSpreadsheet,
} from "lucide-react";

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line } from "react-chartjs-2";

import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";
import {
  predictSales,
  forecastRevenue,
  fetchDatasets,
  fetchModelInfo,
} from "../services/api";

import "../styles/Prediction.css";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  Filler
);

function formatCurrency(amount, currency = "USD") {
  if (amount === undefined || amount === null || isNaN(amount)) return "—";
  const num = Number(amount);
  const curr = (currency || "USD").trim().toUpperCase();

  try {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency: curr,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(num);
  } catch {
    const symbols = {
      USD: "$",
      EUR: "€",
      GBP: "£",
      INR: "₹",
      JPY: "¥",
      CAD: "CA$",
      AUD: "A$",
    };
    const sym = symbols[curr] || `${curr} `;
    return `${sym}${num.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  }
}

function getCurrencySymbol(currency = "USD") {
  const curr = (currency || "USD").trim().toUpperCase();
  const symbols = {
    USD: "$",
    EUR: "€",
    GBP: "£",
    INR: "₹",
    JPY: "¥",
    CAD: "CA$",
    AUD: "A$",
  };
  return symbols[curr] || `${curr} `;
}

function Prediction() {
  // Navigation active tab: 'revenue-forecast' (New) or 'ad-prediction' (Existing)
  const [activeTab, setActiveTab] = useState("revenue-forecast");

  /* =========================================================
     TAB 1 STATE: FINANCIAL REVENUE FORECASTING
  ========================================================= */
  const [datasets, setDatasets] = useState([]);
  const [loadingDatasets, setLoadingDatasets] = useState(true);
  const [selectedDatasetId, setSelectedDatasetId] = useState("");
  const [horizonDays, setHorizonDays] = useState(30);

  const [isForecasting, setIsForecasting] = useState(false);
  const [forecastResult, setForecastResult] = useState(null);
  const [forecastError, setForecastError] = useState(null);

  /* =========================================================
     TAB 2 STATE: ADVERTISING-BASED SALES PREDICTION (PRESERVED)
  ========================================================= */
  const [tv, setTv] = useState("180.8");
  const [radio, setRadio] = useState("10.8");
  const [newspaper, setNewspaper] = useState("58.4");

  const [isAdPredicting, setIsAdPredicting] = useState(false);
  const [adPredictionResult, setAdPredictionResult] = useState(null);
  const [adError, setAdError] = useState(null);
  const [modelInfo, setModelInfo] = useState(null);

  // Load uploaded datasets and model metadata on mount
  useEffect(() => {
    loadDatasetList();
    fetchModelInfo()
      .then((info) => setModelInfo(info))
      .catch((err) => console.warn("Could not load model info:", err));
  }, []);

  async function loadDatasetList() {
    try {
      setLoadingDatasets(true);
      const data = await fetchDatasets();
      const list = Array.isArray(data) ? data : [];
      setDatasets(list);
      if (list.length > 0) {
        setSelectedDatasetId(list[0].id);
      }
    } catch (err) {
      console.error("Failed to load dataset list:", err);
    } finally {
      setLoadingDatasets(false);
    }
  }

  /* ---------------------------------------------------------
     HANDLER: FINANCIAL REVENUE FORECASTING
  --------------------------------------------------------- */
  async function handleForecastSubmit(e, overrideHorizon = null) {
    if (e && e.preventDefault) e.preventDefault();
    if (!selectedDatasetId) {
      setForecastError("Please select an uploaded dataset to generate a forecast.");
      return;
    }

    const targetHorizon = overrideHorizon !== null ? overrideHorizon : horizonDays;

    try {
      setIsForecasting(true);
      setForecastError(null);

      // Pass user's local date (YYYY-MM-DD) so backend dynamically anchors accurately for client's timezone
      const now = new Date();
      const localYear = now.getFullYear();
      const localMonth = String(now.getMonth() + 1).padStart(2, "0");
      const localDay = String(now.getDate()).padStart(2, "0");
      const clientToday = `${localYear}-${localMonth}-${localDay}`;

      const res = await forecastRevenue({
        dataset_id: selectedDatasetId,
        horizon_days: targetHorizon,
        anchor_date: clientToday,
      });

      setForecastResult(res);
    } catch (err) {
      setForecastError(err.message || "Failed to generate revenue forecast.");
    } finally {
      setIsForecasting(false);
    }
  }

  /* ---------------------------------------------------------
     HANDLER: ADVERTISING-BASED SALES PREDICTION
  --------------------------------------------------------- */
  async function handleAdPredictSubmit(e) {
    e.preventDefault();
    if (!tv || !radio || !newspaper) {
      setAdError("Please enter values for TV, Radio, and Newspaper advertising budgets.");
      return;
    }

    try {
      setIsAdPredicting(true);
      setAdError(null);
      setAdPredictionResult(null);

      const res = await predictSales({
        tv: parseFloat(tv),
        radio: parseFloat(radio),
        newspaper: parseFloat(newspaper),
      });

      setAdPredictionResult(res);
    } catch (err) {
      setAdError(err.message || "Failed to generate sales prediction.");
    } finally {
      setIsAdPredicting(false);
    }
  }

  /* =========================================================
     CHART DATA PREPARATION: COMBINED TIME-SERIES
  ========================================================= */
  const forecastChartData = useMemo(() => {
    if (!forecastResult) return null;

    const hist = forecastResult.historical_data || [];
    const fc = forecastResult.forecast_data || [];
    const currency = forecastResult.currency || "USD";

    // Combine labels: historical dates followed by forecast dates
    const histDates = hist.map((p) => p.date);
    const fcDates = fc.map((p) => p.date);
    const allLabels = [...histDates, ...fcDates];

    // Historical dataset: actual values for historical range, null thereafter
    const histSeries = [
      ...hist.map((p) => p.revenue),
      ...Array(fc.length).fill(null),
    ];

    // Determine if the forecast is contiguous with the historical actuals
    // If contiguous (e.g. fc[0] is exactly 1 calendar day after hist[last]), bridge the line.
    // Otherwise, keep historical actuals and forecast separate without drawing a bridge across date gaps (Requirement 5).
    const isContiguous = (() => {
      if (hist.length === 0 || fc.length === 0) return false;
      const lastHistStr = hist[hist.length - 1].date;
      const firstFcStr = fc[0].date;
      const d1 = new Date(lastHistStr);
      const d2 = new Date(firstFcStr);
      const diffMs = d2.getTime() - d1.getTime();
      const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));
      return diffDays === 1;
    })();

    const lastHistVal = hist.length > 0 ? hist[hist.length - 1].revenue : null;
    const padding = Array(isContiguous ? Math.max(0, hist.length - 1) : hist.length).fill(null);

    // Forecast series:
    // If contiguous: [null*(N-1), lastHistVal, ...fcValues]
    // If separated: [null*N, ...fcValues]
    const fcSeries = isContiguous
      ? [...padding, lastHistVal, ...fc.map((p) => p.forecast_revenue)]
      : [...padding, ...fc.map((p) => p.forecast_revenue)];

    // Confidence interval upper and lower bounds
    const upperBoundSeries = isContiguous
      ? [...padding, lastHistVal, ...fc.map((p) => p.upper_bound)]
      : [...padding, ...fc.map((p) => p.upper_bound)];

    const lowerBoundSeries = isContiguous
      ? [...padding, lastHistVal, ...fc.map((p) => p.lower_bound)]
      : [...padding, ...fc.map((p) => p.lower_bound)];

    return {
      labels: allLabels.map((d) => {
        const parts = d.split("-");
        if (parts.length === 3) {
          const monthNames = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
          ];
          const m = parseInt(parts[1], 10) - 1;
          return `${monthNames[m] || parts[1]} ${parts[2]}`;
        }
        return d;
      }),
      datasets: [
        {
          label: `Historical Actual Revenue (${currency})`,
          data: histSeries,
          borderColor: "#2563eb",
          backgroundColor: "#2563eb",
          borderWidth: 2.5,
          tension: 0.25,
          pointRadius: 4,
          pointBackgroundColor: "#2563eb",
          pointHoverRadius: 6,
          fill: false,
        },
        {
          label: `Forecasted Revenue (${currency})`,
          data: fcSeries,
          borderColor: "#059669",
          borderDash: [6, 4],
          backgroundColor: "#059669",
          borderWidth: 2.5,
          tension: 0.25,
          pointRadius: 4,
          pointBackgroundColor: "#059669",
          pointHoverRadius: 6,
          fill: false,
        },
        {
          label: `${forecastResult?.model_metadata?.confidence_interval_level || "80%"} Upper Bound`,
          data: upperBoundSeries,
          borderColor: "rgba(5, 150, 105, 0.25)",
          borderWidth: 1,
          pointRadius: 0,
          fill: "+1",
          backgroundColor: "rgba(5, 150, 105, 0.08)",
        },
        {
          label: `${forecastResult?.model_metadata?.confidence_interval_level || "80%"} Lower Bound`,
          data: lowerBoundSeries,
          borderColor: "rgba(5, 150, 105, 0.25)",
          borderWidth: 1,
          pointRadius: 0,
          fill: false,
        },
      ],
    };
  }, [forecastResult]);

  const currencySym = forecastResult ? getCurrencySymbol(forecastResult.currency) : "$";

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: "index",
      intersect: false,
    },
    plugins: {
      legend: {
        position: "top",
        labels: {
          font: { family: "Inter, sans-serif", size: 12, weight: "500" },
          color: "#475569",
          filter: (item) => !item.text.includes("Bound"),
        },
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const val = context.raw;
            if (val === null || val === undefined) return null;
            const curr = forecastResult?.currency || "USD";
            return ` ${context.dataset.label}: ${formatCurrency(val, curr)}`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: { color: "#eef2f7" },
        ticks: { color: "#64748b", maxRotation: 45 },
      },
      y: {
        beginAtZero: true,
        grid: { color: "#eef2f7" },
        ticks: {
          color: "#64748b",
          callback: (value) => {
            if (value >= 1000000) return `${currencySym}${(value / 1000000).toFixed(1)}M`;
            if (value >= 1000) return `${currencySym}${(value / 1000).toFixed(1)}k`;
            return `${currencySym}${value}`;
          },
        },
      },
    },
  };

  const selectedDatasetObj = datasets.find(
    (d) => String(d.id) === String(selectedDatasetId)
  );

  return (
    <div
      className="prediction-page"
      style={{ display: "flex", minHeight: "100vh", background: "#f8fafc" }}
    >
      <Sidebar />

      <main
        className="prediction-main"
        style={{
          flex: 1,
          padding: "24px 32px",
          maxWidth: "1280px",
          margin: "0 auto",
        }}
      >
        <Navbar />

        {/* Page Header */}
        <div className="prediction-header" style={{ marginBottom: "20px" }}>
          <h1
            style={{
              fontSize: "1.75rem",
              fontWeight: "700",
              color: "#0f172a",
              margin: 0,
            }}
          >
            AI Predictive Intelligence
          </h1>
          <p style={{ color: "#64748b", marginTop: "4px", marginBottom: 0 }}>
            Generate time-series revenue forecasts from uploaded PostgreSQL financial records,
            or simulate sales unit demand from marketing campaign expenditures.
          </p>
        </div>

        {/* Feature Switcher Tabs */}
        <div
          style={{
            display: "flex",
            gap: "10px",
            marginBottom: "24px",
            background: "#ffffff",
            padding: "6px",
            borderRadius: "12px",
            border: "1px solid #e2e8f0",
            width: "fit-content",
            boxShadow: "0 1px 2px rgba(0,0,0,0.04)",
          }}
        >
          <button
            onClick={() => setActiveTab("revenue-forecast")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              padding: "10px 18px",
              borderRadius: "8px",
              border: "none",
              fontWeight: "600",
              fontSize: "14px",
              cursor: "pointer",
              background:
                activeTab === "revenue-forecast" ? "#2563eb" : "transparent",
              color: activeTab === "revenue-forecast" ? "#ffffff" : "#64748b",
              transition: "all 0.2s ease",
            }}
          >
            <TrendingUp size={16} />
            Financial Revenue Forecasting
          </button>

          <button
            onClick={() => setActiveTab("ad-prediction")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              padding: "10px 18px",
              borderRadius: "8px",
              border: "none",
              fontWeight: "600",
              fontSize: "14px",
              cursor: "pointer",
              background:
                activeTab === "ad-prediction" ? "#2563eb" : "transparent",
              color: activeTab === "ad-prediction" ? "#ffffff" : "#64748b",
              transition: "all 0.2s ease",
            }}
          >
            <Tv size={16} />
            Advertising-Based Sales Prediction
          </button>
        </div>

        {/* =========================================================
            FEATURE 1: FINANCIAL REVENUE FORECASTING
        ========================================================= */}
        {activeTab === "revenue-forecast" && (
          <div>
            {/* Setup & Control Card */}
            <div
              style={{
                background: "#ffffff",
                border: "1px solid #e2e8f0",
                borderRadius: "16px",
                padding: "24px",
                marginBottom: "24px",
                boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                  marginBottom: "20px",
                }}
              >
                <div
                  style={{
                    width: "42px",
                    height: "42px",
                    borderRadius: "10px",
                    background: "#eff6ff",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "#2563eb",
                  }}
                >
                  <TrendingUp size={20} />
                </div>
                <div>
                  <h2
                    style={{
                      fontSize: "1.2rem",
                      fontWeight: "700",
                      color: "#1e293b",
                      margin: 0,
                    }}
                  >
                    Dataset-Based Financial Revenue Forecasting
                  </h2>
                  <p
                    style={{
                      fontSize: "0.875rem",
                      color: "#64748b",
                      margin: "2px 0 0",
                    }}
                  >
                    Select an ingested dataset and project daily revenue forward using
                    exponential trend smoothing.
                  </p>
                </div>
              </div>

              {loadingDatasets ? (
                <div style={{ color: "#64748b", fontSize: "14px", padding: "12px 0" }}>
                  <RefreshCw
                    size={16}
                    style={{
                      animation: "spin 1s linear infinite",
                      display: "inline-block",
                      marginRight: "8px",
                    }}
                  />
                  Loading uploaded datasets...
                </div>
              ) : datasets.length === 0 ? (
                <div
                  style={{
                    padding: "20px",
                    background: "#f8fafc",
                    borderRadius: "12px",
                    border: "1px dashed #cbd5e1",
                    textAlign: "center",
                  }}
                >
                  <Database
                    size={28}
                    color="#64748b"
                    style={{ margin: "0 auto 8px", display: "block" }}
                  />
                  <p style={{ color: "#334155", fontWeight: "600", margin: "0 0 6px" }}>
                    No Datasets Available
                  </p>
                  <p style={{ color: "#64748b", fontSize: "13px", margin: "0 0 16px" }}>
                    Please upload a dataset containing dates and revenue in the Upload section.
                  </p>
                  <Link
                    to="/upload"
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "6px",
                      background: "#2563eb",
                      color: "white",
                      padding: "8px 16px",
                      borderRadius: "8px",
                      textDecoration: "none",
                      fontSize: "13px",
                      fontWeight: "600",
                    }}
                  >
                    <FileSpreadsheet size={16} />
                    Go to Upload
                  </Link>
                </div>
              ) : (
                <form onSubmit={handleForecastSubmit}>
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
                      gap: "20px",
                      alignItems: "flex-end",
                    }}
                  >
                    {/* Dataset Dropdown */}
                    <div>
                      <label
                        style={{
                          display: "block",
                          fontSize: "0.875rem",
                          fontWeight: "600",
                          color: "#334155",
                          marginBottom: "6px",
                        }}
                      >
                        Target Dataset
                      </label>
                      <select
                        value={selectedDatasetId}
                        onChange={(e) => setSelectedDatasetId(e.target.value)}
                        style={{
                          width: "100%",
                          padding: "10px 14px",
                          borderRadius: "8px",
                          border: "1px solid #cbd5e1",
                          background: "#f8fafc",
                          fontSize: "0.95rem",
                          fontWeight: "500",
                          color: "#1e293b",
                          cursor: "pointer",
                        }}
                      >
                        {datasets.map((d) => (
                          <option key={d.id} value={d.id}>
                            Dataset #{d.id} — {d.file_name} ({d.file_type.toUpperCase()})
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Forecast Horizon Selector */}
                    <div>
                      <label
                        style={{
                          display: "block",
                          fontSize: "0.875rem",
                          fontWeight: "600",
                          color: "#334155",
                          marginBottom: "6px",
                        }}
                      >
                        Forecast Horizon
                      </label>
                      <div
                        style={{
                          display: "grid",
                          gridTemplateColumns: "repeat(3, 1fr)",
                          gap: "8px",
                        }}
                      >
                        {[7, 30, 90].map((h) => (
                          <button
                            key={h}
                            type="button"
                            onClick={() => {
                              setHorizonDays(h);
                              if (forecastResult) {
                                handleForecastSubmit(null, h);
                              }
                            }}
                            style={{
                              padding: "9px 0",
                              border:
                                horizonDays === h
                                  ? "2px solid #2563eb"
                                  : "1px solid #cbd5e1",
                              background: horizonDays === h ? "#eff6ff" : "#ffffff",
                              color: horizonDays === h ? "#1e40af" : "#475569",
                              borderRadius: "8px",
                              fontSize: "0.875rem",
                              fontWeight: "600",
                              cursor: "pointer",
                              transition: "all 0.15s ease",
                            }}
                          >
                            {h} Days
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Submit Button */}
                    <div>
                      <button
                        type="submit"
                        disabled={isForecasting || !selectedDatasetId}
                        style={{
                          width: "100%",
                          padding: "11px 20px",
                          background: isForecasting ? "#94a3b8" : "#2563eb",
                          color: "white",
                          border: "none",
                          borderRadius: "8px",
                          fontSize: "0.95rem",
                          fontWeight: "600",
                          cursor: isForecasting ? "not-allowed" : "pointer",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          gap: "8px",
                          transition: "background 0.2s ease",
                        }}
                      >
                        {isForecasting ? (
                          <>
                            <RefreshCw
                              size={16}
                              style={{ animation: "spin 1s linear infinite" }}
                            />
                            Generating Forecast...
                          </>
                        ) : (
                          <>
                            <Sparkles size={16} />
                            Generate Revenue Forecast ✦
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </form>
              )}
            </div>

            {/* Error Banner */}
            {forecastError && (
              <div
                style={{
                  background: "#fef2f2",
                  border: "1px solid #fecaca",
                  color: "#b91c1c",
                  borderRadius: "12px",
                  padding: "16px 20px",
                  marginBottom: "24px",
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "12px",
                }}
              >
                <AlertTriangle size={20} color="#dc2626" style={{ flexShrink: 0, marginTop: "2px" }} />
                <div>
                  <h4 style={{ margin: "0 0 4px", fontSize: "0.95rem" }}>
                    Forecasting Request Failed
                  </h4>
                  <p style={{ margin: 0, fontSize: "0.875rem", lineHeight: "1.5" }}>
                    {forecastError}
                  </p>
                </div>
              </div>
            )}

            {/* Forecast Output Display */}
            {forecastResult && (
              <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                {/* Forecast Advisories Banner */}
                {forecastResult.warnings && forecastResult.warnings.length > 0 && (
                  <div
                    style={{
                      background: "#fffbeb",
                      border: "1px solid #fde68a",
                      borderRadius: "12px",
                      padding: "16px 20px",
                      color: "#92400e",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                        fontWeight: "600",
                        marginBottom: "6px",
                      }}
                    >
                      <AlertTriangle size={18} color="#d97706" />
                      <span>Forecast Model Advisories</span>
                    </div>
                    <ul style={{ margin: 0, paddingLeft: "20px", fontSize: "0.875rem" }}>
                      {forecastResult.warnings.map((w, idx) => (
                        <li key={idx} style={{ marginTop: "4px" }}>
                          {w}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* 1. Summary KPI Cards */}
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                    gap: "16px",
                  }}
                >
                  {/* Projected Total Revenue */}
                  <div
                    style={{
                      background: "#ffffff",
                      border: "1px solid #e2e8f0",
                      borderRadius: "14px",
                      padding: "20px",
                    }}
                  >
                    <span style={{ fontSize: "12px", color: "#64748b", fontWeight: "600" }}>
                      TOTAL PROJECTED REVENUE
                    </span>
                    <h2 style={{ fontSize: "24px", color: "#0f172a", margin: "6px 0 2px" }}>
                      {formatCurrency(
                        forecastResult.summary.total_projected_revenue,
                        forecastResult.currency
                      )}
                    </h2>
                    <span style={{ fontSize: "12px", color: "#16a34a", fontWeight: "500" }}>
                      Over next {forecastResult.horizon_days} days
                    </span>
                  </div>

                  {/* Daily Projected Average */}
                  <div
                    style={{
                      background: "#ffffff",
                      border: "1px solid #e2e8f0",
                      borderRadius: "14px",
                      padding: "20px",
                    }}
                  >
                    <span style={{ fontSize: "12px", color: "#64748b", fontWeight: "600" }}>
                      PROJECTED DAILY AVERAGE
                    </span>
                    <h2 style={{ fontSize: "24px", color: "#0f172a", margin: "6px 0 2px" }}>
                      {formatCurrency(
                        forecastResult.summary.average_daily_projected_revenue,
                        forecastResult.currency
                      )}
                    </h2>
                    <span style={{ fontSize: "12px", color: "#64748b" }}>
                      vs {formatCurrency(forecastResult.summary.average_daily_historical_revenue, forecastResult.currency)} historical daily avg
                    </span>
                  </div>

                  {/* Projected Change % */}
                  <div
                    style={{
                      background: "#ffffff",
                      border: "1px solid #e2e8f0",
                      borderRadius: "14px",
                      padding: "20px",
                    }}
                  >
                    <span style={{ fontSize: "12px", color: "#64748b", fontWeight: "600" }}>
                      PROJECTED TREND VS BASELINE
                    </span>
                    <h2
                      style={{
                        fontSize: "24px",
                        margin: "6px 0 2px",
                        color:
                          forecastResult.summary.projected_change_percent >= 0
                            ? "#16a34a"
                            : "#dc2626",
                      }}
                    >
                      {forecastResult.summary.projected_change_percent >= 0 ? "+" : ""}
                      {forecastResult.summary.projected_change_percent}%
                    </h2>
                    <span style={{ fontSize: "12px", color: "#64748b" }}>
                      Based on damped exponential trend
                    </span>
                  </div>

                  {/* Forecast Window */}
                  <div
                    style={{
                      background: "#ffffff",
                      border: "1px solid #e2e8f0",
                      borderRadius: "14px",
                      padding: "20px",
                    }}
                  >
                    <span style={{ fontSize: "12px", color: "#64748b", fontWeight: "600" }}>
                      FORECAST HORIZON WINDOW
                    </span>
                    <h2 style={{ fontSize: "18px", color: "#0f172a", margin: "8px 0 4px" }}>
                      {forecastResult.summary.forecast_start_date} → {forecastResult.summary.forecast_end_date}
                    </h2>
                    <span style={{ fontSize: "12px", color: "#2563eb", fontWeight: "500" }}>
                      {forecastResult.horizon_days} calendar days
                    </span>
                  </div>
                </div>

                {/* 2. Main Time-Series Forecast Chart */}
                <div
                  style={{
                    background: "#ffffff",
                    border: "1px solid #e2e8f0",
                    borderRadius: "16px",
                    padding: "24px",
                    boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                      marginBottom: "16px",
                      flexWrap: "wrap",
                      gap: "10px",
                    }}
                  >
                    <div>
                      <h3
                        style={{
                          fontSize: "1.1rem",
                          fontWeight: "700",
                          color: "#1e293b",
                          margin: 0,
                        }}
                      >
                        Historical Actuals vs. Projected Revenue
                      </h3>
                      <p
                        style={{
                          fontSize: "0.85rem",
                          color: "#64748b",
                          margin: "4px 0 0",
                        }}
                      >
                        Solid blue line: verified historical records; dashed green line:
                        projected future revenue with {forecastResult.model_metadata.confidence_interval_level || "80%"} prediction interval band.
                      </p>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
                      <span
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "6px",
                          fontSize: "12px",
                          fontWeight: "600",
                          color: "#2563eb",
                        }}
                      >
                        <span
                          style={{
                            width: "12px",
                            height: "3px",
                            background: "#2563eb",
                            display: "inline-block",
                          }}
                        />
                        Actual
                      </span>

                      <span
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "6px",
                          fontSize: "12px",
                          fontWeight: "600",
                          color: "#059669",
                        }}
                      >
                        <span
                          style={{
                            width: "12px",
                            height: "3px",
                            background: "#059669",
                            display: "inline-block",
                            borderBottom: "1px dashed #059669",
                          }}
                        />
                        Forecast
                      </span>

                      <span
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "6px",
                          fontSize: "12px",
                          fontWeight: "500",
                          color: "#64748b",
                        }}
                      >
                        <span
                          style={{
                            width: "12px",
                            height: "10px",
                            background: "rgba(5, 150, 105, 0.15)",
                            borderRadius: "2px",
                            display: "inline-block",
                          }}
                        />
                        {forecastResult.model_metadata.confidence_interval_level || "80%"} Interval
                      </span>
                    </div>
                  </div>

                  <div style={{ height: "360px", width: "100%" }}>
                    {forecastChartData && (
                      <Line data={forecastChartData} options={chartOptions} />
                    )}
                  </div>
                </div>

                {/* 3. Methodology, Assumptions & Limitations Card */}
                <div
                  style={{
                    background: "#ffffff",
                    border: "1px solid #e2e8f0",
                    borderRadius: "16px",
                    padding: "24px",
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
                    gap: "24px",
                  }}
                >
                  {/* Methodology */}
                  <div>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                        marginBottom: "12px",
                        color: "#2563eb",
                      }}
                    >
                      <Layers size={18} />
                      <h4
                        style={{
                          fontSize: "0.95rem",
                          fontWeight: "700",
                          color: "#1e293b",
                          margin: 0,
                        }}
                      >
                        Forecasting Methodology
                      </h4>
                    </div>
                    <p style={{ fontSize: "0.85rem", color: "#475569", lineHeight: "1.6", margin: 0 }}>
                      Method:{" "}
                      <strong>
                        {forecastResult.model_metadata.method}
                      </strong>
                      <br />
                      Parameters: Level Smoothing ($\alpha = {forecastResult.model_metadata.smoothing_level_alpha}$),
                      Trend Smoothing ($\beta = {forecastResult.model_metadata.smoothing_trend_beta}$),
                      Damping ($\phi = {forecastResult.model_metadata.damping_phi}$).
                      <br />
                      Interval Level: <strong>{forecastResult.model_metadata.confidence_interval_level || "80%"}</strong>
                      {forecastResult.model_metadata.interval_uncertainty_note && (
                        <span style={{ display: "block", marginTop: "4px", fontSize: "0.8rem", color: "#64748b" }}>
                          {forecastResult.model_metadata.interval_uncertainty_note}
                        </span>
                      )}
                    </p>
                  </div>

                  {/* Held-Out Accuracy Evaluation */}
                  <div>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                        marginBottom: "12px",
                        color: "#16a34a",
                      }}
                    >
                      <ShieldCheck size={18} />
                      <h4
                        style={{
                          fontSize: "0.95rem",
                          fontWeight: "700",
                          color: "#1e293b",
                          margin: 0,
                        }}
                      >
                        Model Accuracy & Evaluation
                      </h4>
                    </div>
                    {forecastResult.model_metadata.held_out_evaluation?.evaluated_on_held_out ? (
                      <div style={{ fontSize: "0.85rem", color: "#475569", lineHeight: "1.6" }}>
                        <div
                          style={{
                            display: "inline-block",
                            background: "#f0fdf4",
                            color: "#15803d",
                            padding: "3px 8px",
                            borderRadius: "6px",
                            fontWeight: "600",
                            fontSize: "11px",
                            marginBottom: "8px",
                          }}
                        >
                          ✓ Out-of-Sample Backtesting Evaluated
                        </div>
                        <div>
                          <strong>MAE:</strong> {formatCurrency(forecastResult.model_metadata.held_out_evaluation.mae, forecastResult.currency)}
                          &nbsp;|&nbsp;
                          <strong>RMSE:</strong> {formatCurrency(forecastResult.model_metadata.held_out_evaluation.rmse, forecastResult.currency)}
                        </div>
                        <p style={{ margin: "4px 0 0", color: "#64748b", fontSize: "0.8rem" }}>
                          {forecastResult.model_metadata.held_out_evaluation.notes}
                        </p>
                      </div>
                    ) : (
                      <div style={{ fontSize: "0.85rem", color: "#475569" }}>
                        <div
                          style={{
                            display: "inline-block",
                            background: "#fffbeb",
                            color: "#b45309",
                            padding: "3px 8px",
                            borderRadius: "6px",
                            fontWeight: "600",
                            fontSize: "11px",
                            marginBottom: "6px",
                          }}
                        >
                          ⚠️ Evaluation Withheld
                        </div>
                        <p style={{ margin: 0, color: "#64748b", fontSize: "0.8rem", lineHeight: "1.5" }}>
                          {forecastResult.model_metadata.held_out_evaluation?.notes}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Assumptions */}
                  <div>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                        marginBottom: "12px",
                        color: "#0891b2",
                      }}
                    >
                      <Info size={18} />
                      <h4
                        style={{
                          fontSize: "0.95rem",
                          fontWeight: "700",
                          color: "#1e293b",
                          margin: 0,
                        }}
                      >
                        Model Assumptions
                      </h4>
                    </div>
                    <ul
                      style={{
                        fontSize: "0.8rem",
                        color: "#475569",
                        paddingLeft: "18px",
                        margin: 0,
                        lineHeight: "1.6",
                      }}
                    >
                      {forecastResult.model_metadata.assumptions?.map((a, i) => (
                        <li key={i}>{a}</li>
                      ))}
                    </ul>
                  </div>

                  {/* Data Limitations */}
                  <div>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                        marginBottom: "12px",
                        color: "#d97706",
                      }}
                    >
                      <AlertTriangle size={18} />
                      <h4
                        style={{
                          fontSize: "0.95rem",
                          fontWeight: "700",
                          color: "#1e293b",
                          margin: 0,
                        }}
                      >
                        Data Limitations
                      </h4>
                    </div>
                    <ul
                      style={{
                        fontSize: "0.8rem",
                        color: "#475569",
                        paddingLeft: "18px",
                        margin: 0,
                        lineHeight: "1.6",
                      }}
                    >
                      {forecastResult.model_metadata.limitations?.map((l, i) => (
                        <li key={i}>{l}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* =========================================================
            FEATURE 2: ADVERTISING-BASED SALES PREDICTION (PRESERVED)
        ========================================================= */}
        {activeTab === "ad-prediction" && (
          <div>
            {adError && (
              <div
                className="error-banner"
                style={{
                  padding: "14px",
                  background: "#fef2f2",
                  border: "1px solid #fecaca",
                  color: "#b91c1c",
                  borderRadius: "8px",
                  marginBottom: "20px",
                }}
              >
                ⚠️ {adError}
              </div>
            )}

            {/* Prediction Setup Form */}
            <div
              className="prediction-card"
              style={{
                background: "#ffffff",
                border: "1px solid #e2e8f0",
                borderRadius: "16px",
                padding: "24px",
                marginBottom: "32px",
                boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
              }}
            >
              <div
                className="card-title"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                  marginBottom: "20px",
                }}
              >
                <div
                  className="prediction-symbol"
                  style={{ fontSize: "1.5rem", color: "#2563eb" }}
                >
                  ✦
                </div>
                <div>
                  <h2
                    style={{
                      fontSize: "1.25rem",
                      fontWeight: "600",
                      color: "#0f172a",
                      margin: 0,
                    }}
                  >
                    Advertising Expenditure Inputs
                  </h2>
                  <p style={{ fontSize: "0.875rem", color: "#64748b", margin: 0 }}>
                    Enter campaign budget allocations in thousands of dollars ($k)
                  </p>
                </div>
              </div>

              <form onSubmit={handleAdPredictSubmit}>
                <div
                  className="prediction-form"
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                    gap: "20px",
                    marginBottom: "24px",
                  }}
                >
                  {/* TV Input */}
                  <div className="form-group">
                    <label
                      style={{
                        display: "block",
                        fontSize: "0.875rem",
                        fontWeight: "600",
                        color: "#334155",
                        marginBottom: "6px",
                      }}
                    >
                      TV Advertising ($k)
                    </label>
                    <input
                      type="number"
                      step="any"
                      value={tv}
                      onChange={(e) => setTv(e.target.value)}
                      placeholder="e.g. 230.1"
                      required
                      style={{
                        width: "100%",
                        padding: "10px 14px",
                        borderRadius: "8px",
                        border: "1px solid #cbd5e1",
                        fontSize: "1rem",
                      }}
                    />
                    <small
                      style={{
                        color: "#64748b",
                        fontSize: "0.75rem",
                        display: "block",
                        marginTop: "4px",
                      }}
                    >
                      Budget for TV campaigns
                    </small>
                  </div>

                  {/* Radio Input */}
                  <div className="form-group">
                    <label
                      style={{
                        display: "block",
                        fontSize: "0.875rem",
                        fontWeight: "600",
                        color: "#334155",
                        marginBottom: "6px",
                      }}
                    >
                      Radio Advertising ($k)
                    </label>
                    <input
                      type="number"
                      step="any"
                      value={radio}
                      onChange={(e) => setRadio(e.target.value)}
                      placeholder="e.g. 37.8"
                      required
                      style={{
                        width: "100%",
                        padding: "10px 14px",
                        borderRadius: "8px",
                        border: "1px solid #cbd5e1",
                        fontSize: "1rem",
                      }}
                    />
                    <small
                      style={{
                        color: "#64748b",
                        fontSize: "0.75rem",
                        display: "block",
                        marginTop: "4px",
                      }}
                    >
                      Budget for Radio broadcasts
                    </small>
                  </div>

                  {/* Newspaper Input */}
                  <div className="form-group">
                    <label
                      style={{
                        display: "block",
                        fontSize: "0.875rem",
                        fontWeight: "600",
                        color: "#334155",
                        marginBottom: "6px",
                      }}
                    >
                      Newspaper Advertising ($k)
                    </label>
                    <input
                      type="number"
                      step="any"
                      value={newspaper}
                      onChange={(e) => setNewspaper(e.target.value)}
                      placeholder="e.g. 69.2"
                      required
                      style={{
                        width: "100%",
                        padding: "10px 14px",
                        borderRadius: "8px",
                        border: "1px solid #cbd5e1",
                        fontSize: "1rem",
                      }}
                    />
                    <small
                      style={{
                        color: "#64748b",
                        fontSize: "0.75rem",
                        display: "block",
                        marginTop: "4px",
                      }}
                    >
                      Budget for Print press
                    </small>
                  </div>
                </div>

                <button
                  type="submit"
                  className="generate-button"
                  disabled={isAdPredicting}
                  style={{
                    background: isAdPredicting ? "#94a3b8" : "#2563eb",
                    color: "#ffffff",
                    padding: "12px 24px",
                    border: "none",
                    borderRadius: "8px",
                    fontSize: "1rem",
                    fontWeight: "600",
                    cursor: isAdPredicting ? "not-allowed" : "pointer",
                  }}
                >
                  {isAdPredicting
                    ? "Running Prediction Model..."
                    : "Predict Sales Units ✦"}
                </button>
              </form>
            </div>

            {/* Results Highlight Card */}
            {adPredictionResult && (
              <div
                className="prediction-results"
                style={{
                  background: "#ffffff",
                  border: "1px solid #bfdbfe",
                  borderRadius: "16px",
                  padding: "28px",
                  boxShadow: "0 4px 6px -1px rgba(0,0,0,0.05)",
                }}
              >
                <div
                  className="results-header"
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "20px",
                  }}
                >
                  <div>
                    <h2
                      style={{
                        fontSize: "1.25rem",
                        color: "#1e3a8a",
                        margin: 0,
                      }}
                    >
                      Predicted Sales Result
                    </h2>
                    <p
                      style={{
                        color: "#64748b",
                        fontSize: "0.875rem",
                        margin: 0,
                      }}
                    >
                      Generated via {modelInfo?.model_name || "Gradient Boosting Regressor"} (R² = {modelInfo?.test_metrics?.r2 ?? "0.9587"})
                    </p>
                  </div>

                  <div
                    style={{
                      background: "#dcfce7",
                      color: "#15803d",
                      padding: "6px 14px",
                      borderRadius: "20px",
                      fontSize: "0.875rem",
                      fontWeight: "600",
                    }}
                  >
                    ✓ Model Inference Complete
                  </div>
                </div>

                {/* Extrapolation Warning Alert (A4 fix) */}
                {adPredictionResult?.extrapolation_warning && (
                  <div
                    style={{
                      background: "#fffbeb",
                      border: "1px solid #fde68a",
                      color: "#92400e",
                      borderRadius: "10px",
                      padding: "12px 16px",
                      marginBottom: "16px",
                      display: "flex",
                      alignItems: "center",
                      gap: "10px",
                    }}
                  >
                    <AlertTriangle size={18} color="#d97706" style={{ flexShrink: 0 }} />
                    <span style={{ fontSize: "0.875rem" }}>
                      {adPredictionResult.extrapolation_warning}
                    </span>
                  </div>
                )}

                {/* Main Prominent Metric */}
                <div
                  style={{
                    background:
                      "linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%)",
                    color: "#ffffff",
                    padding: "32px",
                    borderRadius: "12px",
                    textAlign: "center",
                    marginBottom: "24px",
                  }}
                >
                  <span
                    style={{
                      fontSize: "0.9rem",
                      textTransform: "uppercase",
                      letterSpacing: "1px",
                      opacity: 0.9,
                    }}
                  >
                    Predicted Sales Output
                  </span>
                  <h1
                    style={{
                      fontSize: "3.5rem",
                      fontWeight: "800",
                      margin: "12px 0 4px 0",
                    }}
                  >
                    {adPredictionResult.predicted_sales}{" "}
                    <span style={{ fontSize: "1.5rem", fontWeight: "400" }}>
                      units
                    </span>
                  </h1>
                  <p style={{ fontSize: "0.875rem", opacity: 0.9, margin: 0 }}>
                    Based on ${adPredictionResult.tv}k TV, $
                    {adPredictionResult.radio}k Radio, $
                    {adPredictionResult.newspaper}k Newspaper
                  </p>
                </div>

                {/* Input Feature Breakdown */}
                <div
                  className="prediction-kpis"
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                    gap: "16px",
                  }}
                >
                  <div
                    className="prediction-kpi"
                    style={{
                      background: "#f8fafc",
                      padding: "16px",
                      borderRadius: "8px",
                      border: "1px solid #e2e8f0",
                    }}
                  >
                    <p
                      style={{
                        fontSize: "0.875rem",
                        color: "#64748b",
                        margin: 0,
                      }}
                    >
                      TV Budget
                    </p>
                    <h3
                      style={{
                        fontSize: "1.25rem",
                        color: "#0f172a",
                        margin: "4px 0",
                      }}
                    >
                      ${adPredictionResult.tv}k
                    </h3>
                    <span style={{ fontSize: "0.75rem", color: "#2563eb" }}>
                      Primary contributor
                    </span>
                  </div>

                  <div
                    className="prediction-kpi"
                    style={{
                      background: "#f8fafc",
                      padding: "16px",
                      borderRadius: "8px",
                      border: "1px solid #e2e8f0",
                    }}
                  >
                    <p
                      style={{
                        fontSize: "0.875rem",
                        color: "#64748b",
                        margin: 0,
                      }}
                    >
                      Radio Budget
                    </p>
                    <h3
                      style={{
                        fontSize: "1.25rem",
                        color: "#0f172a",
                        margin: "4px 0",
                      }}
                    >
                      ${adPredictionResult.radio}k
                    </h3>
                    <span style={{ fontSize: "0.75rem", color: "#2563eb" }}>
                      Secondary contributor
                    </span>
                  </div>

                  <div
                    className="prediction-kpi"
                    style={{
                      background: "#f8fafc",
                      padding: "16px",
                      borderRadius: "8px",
                      border: "1px solid #e2e8f0",
                    }}
                  >
                    <p
                      style={{
                        fontSize: "0.875rem",
                        color: "#64748b",
                        margin: 0,
                      }}
                    >
                      Newspaper Budget
                    </p>
                    <h3
                      style={{
                        fontSize: "1.25rem",
                        color: "#0f172a",
                        margin: "4px 0",
                      }}
                    >
                      ${adPredictionResult.newspaper}k
                    </h3>
                    <span style={{ fontSize: "0.75rem", color: "#64748b" }}>
                      Print contribution
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default Prediction;