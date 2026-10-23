import { useState, useEffect, useMemo } from "react";
import { Link } from "react-router-dom";
import {
  BarChart3,
  TrendingUp,
  Database,
  AlertTriangle,
  Copy,
  Download,
  Sparkles,
  RefreshCw,
  CheckCircle2,
  Calendar,
  Layers,
  FileSpreadsheet,
} from "lucide-react";

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Tooltip,
  Legend,
} from "chart.js";

import { Line, Bar } from "react-chartjs-2";

import Sidebar from "../components/Sidebar";
import {
  fetchDatasets,
  fetchDatasetSummary,
  fetchDatasetMetadata,
  fetchDatasetRecords,
} from "../services/api";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Tooltip,
  Legend
);

// Indicative Reference Exchange Rates relative to 1 USD
const FX_RATES_TO_USD = {
  USD: 1.0,
  EUR: 0.92,
  GBP: 0.79,
  INR: 83.50,
  JPY: 155.0,
  CAD: 1.36,
  AUD: 1.52,
};

function getExchangeRate(fromCurrency, toCurrency) {
  const from = (fromCurrency || "USD").toUpperCase();
  const to = (toCurrency || "USD").toUpperCase();
  if (from === to) return 1.0;
  const rateFrom = FX_RATES_TO_USD[from] || 1.0;
  const rateTo = FX_RATES_TO_USD[to] || 1.0;
  return rateTo / rateFrom;
}

// Format currency using explicit exchange rate conversion from dataset base currency
function formatCurrency(amount, targetCurrency = "USD", baseCurrency = "USD") {
  if (amount === undefined || amount === null || isNaN(amount)) return "—";
  const num = Number(amount);
  const target = (targetCurrency || "USD").trim().toUpperCase();
  const base = (baseCurrency || "USD").trim().toUpperCase();
  const rate = getExchangeRate(base, target);
  const converted = num * rate;

  try {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency: target,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(converted);
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
    const sym = symbols[target] || `${target} `;
    return `${sym}${converted.toLocaleString(undefined, {
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

export default function Analytics() {
  const [datasets, setDatasets] = useState([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState(null);
  const [summary, setSummary] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [records, setRecords] = useState([]);

  const [loading, setLoading] = useState(true);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Currency configuration
  const [baseCurrency, setBaseCurrency] = useState("USD");
  const [displayCurrency, setDisplayCurrency] = useState("USD");

  const [trendView, setTrendView] = useState("month"); // 'month' or 'date'
  const [lastUpdated, setLastUpdated] = useState(null);

  // Initial load: fetch dataset list
  useEffect(() => {
    loadDatasets();
  }, []);

  async function loadDatasets() {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchDatasets();
      const list = Array.isArray(data) ? data : [];
      setDatasets(list);

      if (list.length > 0) {
        const firstId = list[0].id;
        setSelectedDatasetId(firstId);
        await loadDatasetDetails(firstId);
      } else {
        setSelectedDatasetId(null);
        setSummary(null);
        setMetadata(null);
        setRecords([]);
      }
    } catch (err) {
      console.error("Failed to load datasets:", err);
      setError(err.message || "Failed to load datasets from backend.");
    } finally {
      setLoading(false);
    }
  }

  async function loadDatasetDetails(datasetId) {
    if (!datasetId) return;
    try {
      setDetailsLoading(true);
      setError(null);

      const [sumRes, metaRes, recRes] = await Promise.allSettled([
        fetchDatasetSummary(datasetId),
        fetchDatasetMetadata(datasetId),
        fetchDatasetRecords(datasetId),
      ]);

      let detectedBase = "USD";
      if (sumRes.status === "fulfilled" && sumRes.value) {
        setSummary(sumRes.value);
        if (sumRes.value.currency) {
          detectedBase = sumRes.value.currency.toUpperCase();
        }
      } else {
        setSummary(null);
      }
      setBaseCurrency(detectedBase);
      setDisplayCurrency(detectedBase);

      if (metaRes.status === "fulfilled" && metaRes.value) {
        setMetadata(metaRes.value);
      } else {
        setMetadata(null);
      }

      let loadedRecords = [];
      if (recRes.status === "fulfilled" && Array.isArray(recRes.value)) {
        loadedRecords = recRes.value;
        setRecords(loadedRecords);

        // Auto-detect optimal trend view: if only 1 month exists, default to 'date'
        const distinctMonths = new Set(
          loadedRecords
            .map((r) => (r.date ? String(r.date).slice(0, 7) : null))
            .filter(Boolean)
        );
        if (distinctMonths.size <= 1 && loadedRecords.length > 1) {
          setTrendView("date");
        } else {
          setTrendView("month");
        }
      } else {
        setRecords([]);
      }

      setLastUpdated(
        new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      );
    } catch (err) {
      console.error("Failed to load dataset details:", err);
      setError(err.message || "Failed to load dataset details.");
    } finally {
      setDetailsLoading(false);
    }
  }

  function handleDatasetChange(e) {
    const id = parseInt(e.target.value, 10);
    setSelectedDatasetId(id);
    loadDatasetDetails(id);
  }

  const selectedDataset = datasets.find((d) => d.id === selectedDatasetId);

  // Profit Margin calculation
  const profitMargin =
    summary && summary.total_revenue > 0
      ? ((summary.total_profit / summary.total_revenue) * 100).toFixed(1)
      : null;

  const currentRate = getExchangeRate(baseCurrency, displayCurrency);
  const isConverted = displayCurrency !== baseCurrency;

  /* =========================================================
     CHART 1: SALES / REVENUE TREND
  ========================================================= */
  const salesData = useMemo(() => {
    if (!records || records.length === 0) {
      return { labels: [], datasets: [] };
    }

    const rate = getExchangeRate(baseCurrency, displayCurrency);

    if (trendView === "date") {
      // Group by daily date (YYYY-MM-DD)
      const dateMap = {};
      records.forEach((r) => {
        const rawDate = r.date ? String(r.date).trim() : "Unknown";
        const rev = typeof r.revenue === "number" ? r.revenue : parseFloat(r.revenue) || 0;
        dateMap[rawDate] = (dateMap[rawDate] || 0) + rev * rate;
      });

      const sortedDates = Object.keys(dateMap).sort();
      const labels = sortedDates.map((d) => {
        const parts = d.split("-");
        if (parts.length === 3) {
          const monthNames = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
          ];
          const mIdx = parseInt(parts[1], 10) - 1;
          return `${monthNames[mIdx] || parts[1]} ${parts[2]}`;
        }
        return d;
      });

      const values = sortedDates.map((d) => Math.round(dateMap[d] * 100) / 100);

      return {
        labels,
        datasets: [
          {
            label: `Revenue (${displayCurrency})`,
            data: values,
            borderColor: "#2563eb",
            backgroundColor: "rgba(37, 99, 235, 0.12)",
            borderWidth: 3,
            fill: true,
            tension: 0.35,
            pointRadius: 5,
            pointBackgroundColor: "#2563eb",
            pointHoverRadius: 7,
          },
        ],
      };
    } else {
      // Group by month (YYYY-MM)
      const monthMap = {};
      records.forEach((r) => {
        let key = "Unknown";
        if (r.date && String(r.date).length >= 7) {
          key = String(r.date).slice(0, 7);
        }
        const rev = typeof r.revenue === "number" ? r.revenue : parseFloat(r.revenue) || 0;
        monthMap[key] = (monthMap[key] || 0) + rev * rate;
      });

      const sortedMonths = Object.keys(monthMap).sort();
      const monthNames = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
      ];
      const labels = sortedMonths.map((m) => {
        const parts = m.split("-");
        if (parts.length === 2) {
          const idx = parseInt(parts[1], 10) - 1;
          return `${monthNames[idx] || parts[1]} ${parts[0]}`;
        }
        return m;
      });

      const values = sortedMonths.map((m) => Math.round(monthMap[m] * 100) / 100);

      return {
        labels,
        datasets: [
          {
            label: `Revenue (${displayCurrency})`,
            data: values,
            borderColor: "#2563eb",
            backgroundColor: "rgba(37, 99, 235, 0.12)",
            borderWidth: 3,
            fill: true,
            tension: 0.35,
            pointRadius: 5,
            pointBackgroundColor: "#2563eb",
            pointHoverRadius: 7,
          },
        ],
      };
    }
  }, [records, trendView, displayCurrency, baseCurrency]);

  /* =========================================================
     CHART 2: REVENUE BY CATEGORY
  ========================================================= */
  const categoryData = useMemo(() => {
    if (!records || records.length === 0) {
      return { labels: [], datasets: [] };
    }

    const rate = getExchangeRate(baseCurrency, displayCurrency);
    const catMap = {};
    records.forEach((r) => {
      let rawCat = r.category;
      if (!rawCat || typeof rawCat !== "string" || !rawCat.trim()) {
        rawCat = "Uncategorized";
      } else {
        rawCat = rawCat.trim();
        rawCat = rawCat
          .split(" ")
          .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
          .join(" ");
      }
      const rev = typeof r.revenue === "number" ? r.revenue : parseFloat(r.revenue) || 0;
      catMap[rawCat] = (catMap[rawCat] || 0) + rev * rate;
    });

    const sortedCategories = Object.keys(catMap).sort(
      (a, b) => catMap[b] - catMap[a]
    );

    const values = sortedCategories.map((c) => Math.round(catMap[c] * 100) / 100);

    const barColors = [
      "#2563eb",
      "#7c3aed",
      "#059669",
      "#d97706",
      "#e11d48",
      "#0891b2",
    ];

    return {
      labels: sortedCategories,
      datasets: [
        {
          label: `Revenue (${displayCurrency})`,
          data: values,
          backgroundColor: sortedCategories.map(
            (_, idx) => barColors[idx % barColors.length]
          ),
          borderRadius: 8,
          borderWidth: 0,
        },
      ],
    };
  }, [records, displayCurrency, baseCurrency]);

  /* =========================================================
     DYNAMIC AI INSIGHTS
  ========================================================= */
  const insights = useMemo(() => {
    if (!summary || !records || records.length === 0) {
      return [];
    }

    const list = [];

    // 1. Revenue & Profit Margin insight
    if (summary.total_revenue !== undefined) {
      const margin =
        summary.total_revenue > 0
          ? ((summary.total_profit / summary.total_revenue) * 100).toFixed(1)
          : "0.0";
      list.push(
        `Total revenue reached ${formatCurrency(summary.total_revenue, displayCurrency, baseCurrency)} generating net profit of ${formatCurrency(summary.total_profit, displayCurrency, baseCurrency)} (${margin}% profit margin).`
      );
    }

    // 2. Leading Category insight
    const catMap = {};
    records.forEach((r) => {
      const cat = (r.category || "Uncategorized").trim();
      const rev = typeof r.revenue === "number" ? r.revenue : parseFloat(r.revenue) || 0;
      catMap[cat] = (catMap[cat] || 0) + rev;
    });
    const sortedCats = Object.entries(catMap).sort((a, b) => b[1] - a[1]);
    if (sortedCats.length > 0 && sortedCats[0][1] > 0) {
      const topName = sortedCats[0][0]
        .split(" ")
        .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
        .join(" ");
      const topRev = sortedCats[0][1];
      const pct = summary.total_revenue > 0 ? ((topRev / summary.total_revenue) * 100).toFixed(1) : "100";
      list.push(
        `${topName} is your highest-grossing category at ${formatCurrency(topRev, displayCurrency, baseCurrency)}, representing ${pct}% of total dataset revenue.`
      );
    }

    // 3. Data Quality & ETL insight
    if (metadata) {
      const score = metadata.data_quality_score ?? 100;
      const dupes = metadata.duplicates_removed || 0;
      const invalid = metadata.invalid_rows || 0;
      list.push(
        `Data quality score is ${score}%. Automated ETL pipeline removed ${dupes} duplicate entries and filtered ${invalid} invalid rows.`
      );
    }

    // 4. Time span insight
    const dates = records
      .map((r) => r.date)
      .filter(Boolean)
      .sort();
    if (dates.length > 0) {
      const minDate = dates[0];
      const maxDate = dates[dates.length - 1];
      if (minDate === maxDate) {
        list.push(`All ${records.length} records are recorded on ${minDate}.`);
      } else {
        list.push(
          `Transaction records span from ${minDate} to ${maxDate} across ${records.length} clean entries.`
        );
      }
    }

    return list;
  }, [summary, records, metadata, displayCurrency, baseCurrency]);

  /* =========================================================
     CHART OPTIONS
  ========================================================= */
  const currencySym = getCurrencySymbol(displayCurrency);

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "top",
        labels: {
          font: { family: "Inter, sans-serif", size: 12, weight: "500" },
          color: "#475569",
        },
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const val = context.raw;
            const rate = getExchangeRate(baseCurrency, displayCurrency);
            // Convert back to base for context disclosure if converted
            const baseVal = rate !== 0 ? val / rate : val;
            let str = ` ${context.dataset.label}: ${formatCurrency(baseVal, displayCurrency, baseCurrency)}`;
            if (isConverted) {
              str += ` (Base: ${formatCurrency(baseVal, baseCurrency, baseCurrency)})`;
            }
            return str;
          },
        },
      },
    },
    scales: {
      x: {
        grid: { color: "#eef2f7" },
        ticks: { color: "#64748b" },
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

  /* =========================================================
     EXPORT REPORT HANDLER
  ========================================================= */
  function handleExportReport() {
    if (!selectedDataset || !summary) return;

    const reportData = {
      export_timestamp: new Date().toISOString(),
      dataset: {
        id: selectedDataset.id,
        file_name: selectedDataset.file_name,
        file_type: selectedDataset.file_type,
        status: selectedDataset.status,
      },
      base_currency: baseCurrency,
      display_currency: displayCurrency,
      conversion_rate_applied: currentRate,
      summary: {
        total_revenue_base: summary.total_revenue,
        total_revenue_display: summary.total_revenue * currentRate,
        total_expenses_base: summary.total_expenses,
        total_expenses_display: summary.total_expenses * currentRate,
        total_profit_base: summary.total_profit,
        total_profit_display: summary.total_profit * currentRate,
        records_count: summary.records,
        data_quality_score: summary.data_quality_score,
      },
      metadata: metadata || null,
      records: records || [],
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${selectedDataset.file_name.replace(/\.[^/.]+$/, "")}_analytics_report.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#f4f7fe",
        overflowX: "hidden",
      }}
    >
      {/* SIDEBAR */}
      <Sidebar />

      {/* MAIN ANALYTICS AREA */}
      <div
        style={{
          marginLeft: "274px",
          width: "calc(100% - 274px)",
          minHeight: "100vh",
          position: "relative",
          zIndex: 1,
        }}
      >
        {/* HEADER */}
        <header
          style={{
            background: "#ffffff",
            borderBottom: "1px solid #e2e8f0",
            padding: "24px 32px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "16px",
          }}
        >
          <div>
            <p
              style={{
                fontSize: "13px",
                color: "#94a3b8",
                marginBottom: "5px",
              }}
            >
              NexusAI / Analytics
            </p>

            <h1
              style={{
                fontSize: "28px",
                fontWeight: "700",
                color: "#1e293b",
                margin: 0,
              }}
            >
              Analytics Overview
            </h1>

            <p
              style={{
                fontSize: "14px",
                color: "#64748b",
                marginTop: "6px",
                marginBottom: 0,
              }}
            >
              Monitor genuine business KPIs, dataset revenue trends, and data quality metrics
            </p>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            {/* Refresh Button */}
            <button
              onClick={() => {
                if (selectedDatasetId) {
                  loadDatasetDetails(selectedDatasetId);
                } else {
                  loadDatasets();
                }
              }}
              disabled={detailsLoading || loading}
              title="Refresh Analytics"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                background: "#f1f5f9",
                color: "#475569",
                border: "1px solid #cbd5e1",
                borderRadius: "10px",
                padding: "11px 16px",
                fontSize: "14px",
                fontWeight: "600",
                cursor: detailsLoading || loading ? "not-allowed" : "pointer",
                transition: "all 0.2s ease",
              }}
            >
              <RefreshCw
                size={16}
                style={{
                  animation: detailsLoading || loading ? "spin 1s linear infinite" : "none",
                }}
              />
              Refresh
            </button>

            {/* Export Report Button */}
            <button
              onClick={handleExportReport}
              disabled={!summary || records.length === 0}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                background: summary && records.length > 0 ? "#2563eb" : "#94a3b8",
                color: "white",
                border: "none",
                borderRadius: "10px",
                padding: "11px 18px",
                fontSize: "14px",
                fontWeight: "600",
                cursor: summary && records.length > 0 ? "pointer" : "not-allowed",
              }}
            >
              <Download size={18} />
              Export Report
            </button>
          </div>
        </header>

        {/* CONTENT */}
        <main style={{ padding: "28px 32px" }}>
          {/* Error Banner */}
          {error && (
            <div
              style={{
                background: "#fef2f2",
                border: "1px solid #fecaca",
                color: "#b91c1c",
                borderRadius: "12px",
                padding: "16px 20px",
                marginBottom: "24px",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "12px",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <AlertTriangle size={20} color="#dc2626" />
                <span>{error}</span>
              </div>
              <button
                onClick={() => loadDatasets()}
                style={{
                  background: "#dc2626",
                  color: "white",
                  border: "none",
                  borderRadius: "6px",
                  padding: "6px 14px",
                  fontSize: "13px",
                  fontWeight: "600",
                  cursor: "pointer",
                }}
              >
                Retry
              </button>
            </div>
          )}

          {/* Loading State */}
          {loading ? (
            <div
              style={{
                background: "#ffffff",
                border: "1px solid #e2e8f0",
                borderRadius: "16px",
                padding: "60px 20px",
                textAlign: "center",
                color: "#64748b",
              }}
            >
              <RefreshCw
                size={36}
                color="#2563eb"
                style={{
                  animation: "spin 1s linear infinite",
                  margin: "0 auto 16px",
                  display: "block",
                }}
              />
              <h3 style={{ margin: "0 0 6px", color: "#1e293b", fontSize: "18px" }}>
                Loading Datasets...
              </h3>
              <p style={{ margin: 0, fontSize: "14px" }}>
                Connecting to backend and fetching PostgreSQL dataset records
              </p>
            </div>
          ) : datasets.length === 0 ? (
            /* Clear Empty State */
            <div
              style={{
                background: "#ffffff",
                border: "1px dashed #cbd5e1",
                borderRadius: "16px",
                padding: "60px 24px",
                textAlign: "center",
              }}
            >
              <div
                style={{
                  width: "64px",
                  height: "64px",
                  borderRadius: "16px",
                  background: "#eff6ff",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  margin: "0 auto 18px",
                }}
              >
                <Database size={32} color="#2563eb" />
              </div>
              <h2
                style={{
                  fontSize: "20px",
                  fontWeight: "700",
                  color: "#1e293b",
                  margin: "0 0 8px",
                }}
              >
                No Datasets Uploaded Yet
              </h2>
              <p
                style={{
                  fontSize: "14px",
                  color: "#64748b",
                  maxWidth: "460px",
                  margin: "0 auto 24px",
                  lineHeight: "1.5",
                }}
              >
                Upload your CSV or Excel dataset to activate automated ETL cleaning,
                financial KPI aggregation, and interactive analytics charts.
              </p>
              <Link
                to="/upload"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "8px",
                  background: "#2563eb",
                  color: "white",
                  padding: "12px 24px",
                  borderRadius: "10px",
                  textDecoration: "none",
                  fontWeight: "600",
                  fontSize: "14px",
                }}
              >
                <FileSpreadsheet size={18} />
                Go to Upload Dataset
              </Link>
            </div>
          ) : (
            <>
              {/* =================================================
                  DATASET SELECTOR & STATUS BAR
              ================================================= */}
              <div
                style={{
                  background: "#ffffff",
                  border: "1px solid #e2e8f0",
                  borderRadius: "16px",
                  padding: "20px 24px",
                  marginBottom: "20px",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  flexWrap: "wrap",
                  gap: "16px",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "14px",
                    flex: 1,
                    minWidth: "260px",
                  }}
                >
                  <div
                    style={{
                      width: "46px",
                      height: "46px",
                      borderRadius: "12px",
                      background: "#eff6ff",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                    }}
                  >
                    <Database size={22} color="#2563eb" />
                  </div>

                  <div style={{ flex: 1 }}>
                    <p
                      style={{
                        fontSize: "11px",
                        color: "#94a3b8",
                        margin: 0,
                        fontWeight: "600",
                        letterSpacing: "0.5px",
                      }}
                    >
                      SELECTED DATASET
                    </p>

                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "10px",
                        marginTop: "4px",
                        flexWrap: "wrap",
                      }}
                    >
                      <select
                        value={selectedDatasetId || ""}
                        onChange={handleDatasetChange}
                        style={{
                          fontSize: "15px",
                          fontWeight: "600",
                          color: "#1e293b",
                          padding: "6px 12px",
                          borderRadius: "8px",
                          border: "1px solid #cbd5e1",
                          background: "#f8fafc",
                          cursor: "pointer",
                          maxWidth: "340px",
                        }}
                      >
                        {datasets.map((d) => (
                          <option key={d.id} value={d.id}>
                            Dataset #{d.id} — {d.file_name} ({d.file_type.toUpperCase()})
                          </option>
                        ))}
                      </select>

                      {selectedDataset && (
                        <span
                          style={{
                            fontSize: "12px",
                            fontWeight: "600",
                            color:
                              selectedDataset.status === "completed"
                                ? "#16a34a"
                                : "#2563eb",
                            background:
                              selectedDataset.status === "completed"
                                ? "#f0fdf4"
                                : "#eff6ff",
                            padding: "3px 10px",
                            borderRadius: "12px",
                            textTransform: "capitalize",
                          }}
                        >
                          ● {selectedDataset.status}
                        </span>
                      )}

                      <span
                        style={{
                          fontSize: "12px",
                          fontWeight: "500",
                          color: "#64748b",
                          background: "#f1f5f9",
                          padding: "3px 8px",
                          borderRadius: "6px",
                        }}
                      >
                        Base: {baseCurrency} ({getCurrencySymbol(baseCurrency)})
                      </span>
                    </div>
                  </div>
                </div>

                {/* Explicitly Labelled Currency Selector & Meta Info */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "20px",
                    flexWrap: "wrap",
                  }}
                >
                  {/* Currency Conversion Picker */}
                  <div style={{ textAlign: "right" }}>
                    <p
                      style={{
                        fontSize: "11px",
                        color: "#94a3b8",
                        margin: 0,
                        fontWeight: "600",
                        letterSpacing: "0.5px",
                      }}
                    >
                      CURRENCY DISPLAY / FX
                    </p>
                    <select
                      value={displayCurrency}
                      onChange={(e) => setDisplayCurrency(e.target.value)}
                      title="Select currency. Values are converted from dataset base currency using explicit reference exchange rates."
                      style={{
                        fontSize: "13px",
                        fontWeight: "600",
                        color: "#1e293b",
                        padding: "4px 8px",
                        borderRadius: "6px",
                        border: "1px solid #cbd5e1",
                        background: "#f8fafc",
                        marginTop: "3px",
                        cursor: "pointer",
                      }}
                    >
                      <option value={baseCurrency}>
                        {baseCurrency} ({getCurrencySymbol(baseCurrency)}) — Native Base
                      </option>
                      {Object.keys(FX_RATES_TO_USD)
                        .filter((c) => c !== baseCurrency)
                        .map((c) => {
                          const rate = getExchangeRate(baseCurrency, c);
                          return (
                            <option key={c} value={c}>
                              {c} ({getCurrencySymbol(c)}) — 1 {baseCurrency} = {rate.toFixed(2)} {c}
                            </option>
                          );
                        })}
                    </select>
                  </div>

                  {/* Last updated timestamp */}
                  <div style={{ textAlign: "right" }}>
                    <p
                      style={{
                        fontSize: "11px",
                        color: "#94a3b8",
                        margin: 0,
                        fontWeight: "600",
                      }}
                    >
                      LAST UPDATED
                    </p>
                    <p
                      style={{
                        fontSize: "13px",
                        color: "#334155",
                        margin: "4px 0 0",
                        fontWeight: "600",
                      }}
                    >
                      {lastUpdated ? `Today, ${lastUpdated}` : "Just now"}
                    </p>
                  </div>
                </div>
              </div>

              {/* Currency Conversion Explicit Disclosure Banner */}
              {isConverted && (
                <div
                  style={{
                    background: "#eff6ff",
                    border: "1px solid #bfdbfe",
                    borderRadius: "12px",
                    padding: "10px 16px",
                    marginBottom: "20px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    flexWrap: "wrap",
                    gap: "8px",
                    fontSize: "12px",
                    color: "#1e40af",
                  }}
                >
                  <div>
                    <strong>✦ Active Currency Conversion:</strong> Display values converted from dataset base{" "}
                    <strong>{baseCurrency}</strong> using indicative exchange rate assumption:{" "}
                    <strong>1 {baseCurrency} = {currentRate.toFixed(2)} {displayCurrency}</strong>.
                    Original unadjusted dataset revenue is{" "}
                    <strong>{formatCurrency(summary?.total_revenue, baseCurrency, baseCurrency)}</strong>.
                  </div>
                  <button
                    onClick={() => setDisplayCurrency(baseCurrency)}
                    style={{
                      background: "transparent",
                      border: "none",
                      color: "#2563eb",
                      textDecoration: "underline",
                      cursor: "pointer",
                      fontWeight: "600",
                      fontSize: "12px",
                      padding: 0,
                    }}
                  >
                    Reset to Native ({baseCurrency})
                  </button>
                </div>
              )}

              {/* =================================================
                  KPI CARDS (GENUINE BACKEND METRICS)
              ================================================= */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
                  gap: "20px",
                  marginBottom: "24px",
                }}
              >
                {/* 1. TOTAL REVENUE */}
                <KpiCard
                  icon={<TrendingUp size={21} />}
                  iconBg="#eff6ff"
                  iconColor="#2563eb"
                  title="Total Revenue"
                  value={
                    detailsLoading
                      ? "..."
                      : summary && summary.total_revenue !== undefined
                      ? formatCurrency(summary.total_revenue, displayCurrency, baseCurrency)
                      : "—"
                  }
                  growth={
                    summary && summary.total_revenue > 0 ? "100% of Sales" : null
                  }
                />

                {/* 2. TOTAL EXPENSES */}
                <KpiCard
                  icon={<BarChart3 size={21} />}
                  iconBg="#fef2f2"
                  iconColor="#dc2626"
                  title="Total Expenses"
                  value={
                    detailsLoading
                      ? "..."
                      : summary && summary.total_expenses !== undefined
                      ? formatCurrency(summary.total_expenses, displayCurrency, baseCurrency)
                      : "—"
                  }
                  growth={
                    summary && summary.total_revenue > 0
                      ? `${((summary.total_expenses / summary.total_revenue) * 100).toFixed(1)}% Ratio`
                      : null
                  }
                />

                {/* 3. TOTAL PROFIT */}
                <KpiCard
                  icon={<TrendingUp size={21} />}
                  iconBg="#f0fdf4"
                  iconColor="#16a34a"
                  title="Total Profit"
                  value={
                    detailsLoading
                      ? "..."
                      : summary && summary.total_profit !== undefined
                      ? formatCurrency(summary.total_profit, displayCurrency, baseCurrency)
                      : "—"
                  }
                  growth={
                    profitMargin !== null
                      ? `${Number(profitMargin) >= 0 ? "+" : ""}${profitMargin}% Margin`
                      : null
                  }
                />

                {/* 4. NUMBER OF RECORDS */}
                <KpiCard
                  icon={<Layers size={21} />}
                  iconBg="#f5f3ff"
                  iconColor="#7c3aed"
                  title="Clean Records"
                  value={
                    detailsLoading
                      ? "..."
                      : summary && summary.records !== undefined
                      ? summary.records.toLocaleString()
                      : records.length.toLocaleString()
                  }
                  growth={
                    metadata && metadata.total_rows
                      ? `from ${metadata.total_rows} raw`
                      : "Verified"
                  }
                />
              </div>

              {/* =================================================
                  CHARTS SECTION
              ================================================= */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
                  gap: "24px",
                  marginBottom: "24px",
                }}
              >
                {/* 1. SALES / REVENUE TREND */}
                <div
                  style={{
                    background: "#ffffff",
                    border: "1px solid #e2e8f0",
                    borderRadius: "16px",
                    padding: "22px",
                    minWidth: 0,
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                      marginBottom: "18px",
                      flexWrap: "wrap",
                      gap: "10px",
                    }}
                  >
                    <div>
                      <h2
                        style={{
                          fontSize: "18px",
                          fontWeight: "600",
                          color: "#1e293b",
                          margin: 0,
                        }}
                      >
                        Sales Trend
                      </h2>

                      <p
                        style={{
                          fontSize: "13px",
                          color: "#64748b",
                          marginTop: "5px",
                          marginBottom: 0,
                        }}
                      >
                        Revenue performance grouped by {trendView === "month" ? "month" : "date"}
                      </p>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      {/* Trend Granularity Toggle */}
                      <div
                        style={{
                          display: "inline-flex",
                          background: "#f1f5f9",
                          borderRadius: "8px",
                          padding: "2px",
                        }}
                      >
                        <button
                          onClick={() => setTrendView("month")}
                          style={{
                            border: "none",
                            background: trendView === "month" ? "#ffffff" : "transparent",
                            color: trendView === "month" ? "#1e293b" : "#64748b",
                            fontWeight: "600",
                            fontSize: "12px",
                            padding: "4px 10px",
                            borderRadius: "6px",
                            cursor: "pointer",
                            boxShadow: trendView === "month" ? "0 1px 2px rgba(0,0,0,0.06)" : "none",
                          }}
                        >
                          Monthly
                        </button>
                        <button
                          onClick={() => setTrendView("date")}
                          style={{
                            border: "none",
                            background: trendView === "date" ? "#ffffff" : "transparent",
                            color: trendView === "date" ? "#1e293b" : "#64748b",
                            fontWeight: "600",
                            fontSize: "12px",
                            padding: "4px 10px",
                            borderRadius: "6px",
                            cursor: "pointer",
                            boxShadow: trendView === "date" ? "0 1px 2px rgba(0,0,0,0.06)" : "none",
                          }}
                        >
                          By Date
                        </button>
                      </div>

                      <div
                        style={{
                          width: "38px",
                          height: "38px",
                          borderRadius: "10px",
                          background: "#f0fdf4",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                        }}
                      >
                        <TrendingUp size={18} color="#16a34a" />
                      </div>
                    </div>
                  </div>

                  <div style={{ height: "300px", width: "100%" }}>
                    {detailsLoading ? (
                      <div
                        style={{
                          height: "100%",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          color: "#94a3b8",
                        }}
                      >
                        <RefreshCw
                          size={24}
                          color="#2563eb"
                          style={{ animation: "spin 1s linear infinite" }}
                        />
                      </div>
                    ) : salesData.labels.length > 0 ? (
                      <Line data={salesData} options={chartOptions} />
                    ) : (
                      <div
                        style={{
                          height: "100%",
                          display: "flex",
                          flexDirection: "column",
                          alignItems: "center",
                          justifyContent: "center",
                          color: "#94a3b8",
                        }}
                      >
                        <Calendar size={32} style={{ marginBottom: "8px" }} />
                        <p style={{ margin: 0, fontSize: "14px" }}>
                          No date records found in this dataset
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                {/* 2. REVENUE BY CATEGORY */}
                <div
                  style={{
                    background: "#ffffff",
                    border: "1px solid #e2e8f0",
                    borderRadius: "16px",
                    padding: "22px",
                    minWidth: 0,
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                      marginBottom: "18px",
                    }}
                  >
                    <div>
                      <h2
                        style={{
                          fontSize: "18px",
                          fontWeight: "600",
                          color: "#1e293b",
                          margin: 0,
                        }}
                      >
                        Revenue by Category
                      </h2>

                      <p
                        style={{
                          fontSize: "13px",
                          color: "#64748b",
                          marginTop: "5px",
                          marginBottom: 0,
                        }}
                      >
                        Financial distribution across categories
                      </p>
                    </div>

                    <div
                      style={{
                        width: "38px",
                        height: "38px",
                        borderRadius: "10px",
                        background: "#eff6ff",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                    >
                      <BarChart3 size={18} color="#2563eb" />
                    </div>
                  </div>

                  <div style={{ height: "300px", width: "100%" }}>
                    {detailsLoading ? (
                      <div
                        style={{
                          height: "100%",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          color: "#94a3b8",
                        }}
                      >
                        <RefreshCw
                          size={24}
                          color="#2563eb"
                          style={{ animation: "spin 1s linear infinite" }}
                        />
                      </div>
                    ) : categoryData.labels.length > 0 ? (
                      <Bar data={categoryData} options={chartOptions} />
                    ) : (
                      <div
                        style={{
                          height: "100%",
                          display: "flex",
                          flexDirection: "column",
                          alignItems: "center",
                          justifyContent: "center",
                          color: "#94a3b8",
                        }}
                      >
                        <Layers size={32} style={{ marginBottom: "8px" }} />
                        <p style={{ margin: 0, fontSize: "14px" }}>
                          No categories identified in this dataset
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* =================================================
                  BOTTOM CARDS: AI INSIGHTS & DATA QUALITY
              ================================================= */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
                  gap: "24px",
                }}
              >
                {/* AI INSIGHTS (GENUINE AUTOMATED OBSERVATIONS) */}
                <div
                  style={{
                    background: "#ffffff",
                    border: "1px solid #e2e8f0",
                    borderRadius: "16px",
                    padding: "22px",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "12px",
                      marginBottom: "18px",
                    }}
                  >
                    <div
                      style={{
                        width: "42px",
                        height: "42px",
                        borderRadius: "11px",
                        background: "#eff6ff",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                    >
                      <Sparkles size={20} color="#2563eb" />
                    </div>

                    <div>
                      <h2
                        style={{
                          fontSize: "18px",
                          color: "#1e293b",
                          margin: 0,
                          fontWeight: "600",
                        }}
                      >
                        Automated AI Insights
                      </h2>

                      <p
                        style={{
                          fontSize: "12px",
                          color: "#64748b",
                          marginTop: "3px",
                          marginBottom: 0,
                        }}
                      >
                        Dynamic observations computed from current dataset
                      </p>
                    </div>
                  </div>

                  {detailsLoading ? (
                    <div style={{ padding: "20px", textAlign: "center", color: "#94a3b8" }}>
                      Generating insights...
                    </div>
                  ) : insights.length > 0 ? (
                    insights.map((txt, idx) => <Insight key={idx} text={txt} />)
                  ) : (
                    <Insight text="Dataset transaction data will automatically generate real-time AI observations when records are available." />
                  )}
                </div>

                {/* DATA QUALITY (REAL METADATA METRICS) */}
                <div
                  style={{
                    background: "#ffffff",
                    border: "1px solid #e2e8f0",
                    borderRadius: "16px",
                    padding: "22px",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                      marginBottom: "18px",
                    }}
                  >
                    <div>
                      <h2
                        style={{
                          fontSize: "18px",
                          color: "#1e293b",
                          margin: 0,
                          fontWeight: "600",
                        }}
                      >
                        Data Quality & ETL Health
                      </h2>

                      <p
                        style={{
                          fontSize: "12px",
                          color: "#64748b",
                          marginTop: "4px",
                          marginBottom: 0,
                        }}
                      >
                        Automated cleaning and schema validation metrics
                      </p>
                    </div>

                    <span
                      style={{
                        fontSize: "20px",
                        fontWeight: "700",
                        color:
                          (metadata?.data_quality_score ?? 100) >= 80
                            ? "#16a34a"
                            : (metadata?.data_quality_score ?? 100) >= 60
                            ? "#d97706"
                            : "#dc2626",
                      }}
                    >
                      {metadata?.data_quality_score !== null &&
                      metadata?.data_quality_score !== undefined
                        ? `${metadata.data_quality_score}%`
                        : "N/A"}
                    </span>
                  </div>

                  {/* PROGRESS BAR */}
                  <div
                    style={{
                      width: "100%",
                      height: "10px",
                      background: "#e2e8f0",
                      borderRadius: "20px",
                      overflow: "hidden",
                    }}
                  >
                    <div
                      style={{
                        width: `${Math.min(
                          100,
                          Math.max(0, metadata?.data_quality_score || 0)
                        )}%`,
                        height: "100%",
                        background:
                          (metadata?.data_quality_score ?? 100) >= 80
                            ? "#16a34a"
                            : (metadata?.data_quality_score ?? 100) >= 60
                            ? "#d97706"
                            : "#dc2626",
                        borderRadius: "20px",
                        transition: "width 0.5s ease",
                      }}
                    />
                  </div>

                  {/* QUALITY STATS */}
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(4, 1fr)",
                      gap: "12px",
                      marginTop: "25px",
                    }}
                  >
                    <QualityStat
                      icon={<CheckCircle2 size={16} />}
                      color="#16a34a"
                      title="Cleaned"
                      value={
                        metadata?.cleaned_rows !== undefined
                          ? metadata.cleaned_rows.toLocaleString()
                          : records.length.toLocaleString()
                      }
                    />

                    <QualityStat
                      icon={<Copy size={16} />}
                      color="#ef4444"
                      title="Duplicates"
                      value={
                        metadata?.duplicates_removed !== undefined
                          ? metadata.duplicates_removed.toLocaleString()
                          : "0"
                      }
                    />

                    <QualityStat
                      icon={<AlertTriangle size={16} />}
                      color="#d97706"
                      title="Invalid"
                      value={
                        metadata?.invalid_rows !== undefined
                          ? metadata.invalid_rows.toLocaleString()
                          : "0"
                      }
                    />

                    <QualityStat
                      icon={<Database size={16} />}
                      color="#2563eb"
                      title="Total Rows"
                      value={
                        metadata?.total_rows !== undefined
                          ? metadata.total_rows.toLocaleString()
                          : "—"
                      }
                    />
                  </div>
                </div>
              </div>
            </>
          )}
        </main>
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

/* =========================================================
   KPI CARD COMPONENT
========================================================= */
function KpiCard({ icon, iconBg, iconColor, title, value, growth }) {
  return (
    <div
      style={{
        background: "#ffffff",
        border: "1px solid #e2e8f0",
        borderRadius: "16px",
        padding: "20px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div
          style={{
            width: "42px",
            height: "42px",
            borderRadius: "11px",
            background: iconBg,
            color: iconColor,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          {icon}
        </div>

        {growth && (
          <span
            style={{
              fontSize: "12px",
              fontWeight: "600",
              color: growth.includes("-") ? "#dc2626" : "#16a34a",
              background: growth.includes("-") ? "#fef2f2" : "#f0fdf4",
              padding: "2px 8px",
              borderRadius: "6px",
            }}
          >
            {growth}
          </span>
        )}
      </div>

      <div>
        <p
          style={{
            fontSize: "13px",
            color: "#64748b",
            marginTop: "16px",
            marginBottom: "4px",
          }}
        >
          {title}
        </p>

        <h2
          style={{
            fontSize: "24px",
            fontWeight: "700",
            color: "#1e293b",
            margin: 0,
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {value}
        </h2>
      </div>
    </div>
  );
}

/* =========================================================
   INSIGHT COMPONENT
========================================================= */
function Insight({ text }) {
  return (
    <div
      style={{
        background: "#f8fafc",
        borderRadius: "11px",
        padding: "13px 15px",
        marginBottom: "10px",
        display: "flex",
        alignItems: "flex-start",
        gap: "10px",
        border: "1px solid #f1f5f9",
      }}
    >
      <span style={{ color: "#2563eb", fontSize: "14px", lineHeight: "1.6" }}>
        ✦
      </span>
      <p
        style={{
          fontSize: "13px",
          lineHeight: "1.6",
          color: "#475569",
          margin: 0,
        }}
      >
        {text}
      </p>
    </div>
  );
}

/* =========================================================
   DATA QUALITY STAT COMPONENT
========================================================= */
function QualityStat({ icon, color, title, value }) {
  return (
    <div
      style={{
        background: "#f8fafc",
        padding: "10px 12px",
        borderRadius: "8px",
        border: "1px solid #f1f5f9",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "6px",
          color,
          marginBottom: "4px",
        }}
      >
        {icon}
        <span
          style={{
            fontSize: "11px",
            color: "#64748b",
            fontWeight: "500",
          }}
        >
          {title}
        </span>
      </div>

      <p
        style={{
          fontSize: "18px",
          fontWeight: "700",
          color: "#1e293b",
          margin: 0,
        }}
      >
        {value}
      </p>
    </div>
  );
}