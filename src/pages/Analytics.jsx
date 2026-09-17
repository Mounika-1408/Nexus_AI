import {
  BarChart3,
  TrendingUp,
  Database,
  AlertTriangle,
  Copy,
  Download,
  Sparkles,
  Users,
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

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Tooltip,
  Legend
);

export default function Analytics() {
  /* =========================
     SALES DATA
  ========================= */

  const salesData = {
    labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],

    datasets: [
      {
        label: "Revenue",
        data: [42000, 38000, 50000, 61000, 73000, 82000],
        borderWidth: 3,
        tension: 0.4,
        pointRadius: 4,
      },
    ],
  };


  /* =========================
     PRODUCT DATA
  ========================= */

  const productData = {
    labels: [
      "Product A",
      "Product B",
      "Product C",
      "Product D",
    ],

    datasets: [
      {
        label: "Sales",
        data: [45000, 38000, 29000, 22000],
        borderRadius: 8,
      },
    ],
  };


  /* =========================
     CHART OPTIONS
  ========================= */

  const options = {
    responsive: true,
    maintainAspectRatio: false,

    plugins: {
      legend: {
        position: "top",
      },
    },

    scales: {
      x: {
        grid: {
          color: "#eef2f7",
        },
      },

      y: {
        beginAtZero: true,

        grid: {
          color: "#eef2f7",
        },
      },
    },
  };


  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#f4f7fe",
        overflowX: "hidden",
      }}
    >

      {/* =================================================
          SIDEBAR
          KEEP YOUR EXISTING SIDEBAR
      ================================================= */}

      <Sidebar />


      {/* =================================================
          MAIN ANALYTICS AREA

          Sidebar width = 274px
      ================================================= */}

      <div
        style={{
          marginLeft: "274px",
          width: "calc(100% - 274px)",
          minHeight: "100vh",
          position: "relative",
          zIndex: 1,
        }}
      >

        {/* =================================================
            HEADER
        ================================================= */}

        <header
          style={{
            background: "#ffffff",
            borderBottom: "1px solid #e2e8f0",
            padding: "24px 32px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
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
              }}
            >
              Monitor your business performance and discover insights
            </p>

          </div>


          <button
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              background: "#2563eb",
              color: "white",
              border: "none",
              borderRadius: "10px",
              padding: "11px 18px",
              fontSize: "14px",
              fontWeight: "600",
              cursor: "pointer",
            }}
          >

            <Download size={18} />

            Export Report

          </button>

        </header>


        {/* =================================================
            CONTENT
        ================================================= */}

        <main
          style={{
            padding: "28px 32px",
          }}
        >


          {/* =================================================
              DATASET
          ================================================= */}

          <div
            style={{
              background: "#ffffff",
              border: "1px solid #e2e8f0",
              borderRadius: "16px",
              padding: "20px",
              marginBottom: "24px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "14px",
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
                }}
              >

                <Database
                  size={22}
                  color="#2563eb"
                />

              </div>


              <div>

                <p
                  style={{
                    fontSize: "11px",
                    color: "#94a3b8",
                    margin: 0,
                  }}
                >
                  CURRENT DATASET
                </p>

                <h3
                  style={{
                    fontSize: "16px",
                    color: "#1e293b",
                    margin: "4px 0 0",
                  }}
                >
                  Sales_2026.csv
                </h3>

              </div>

            </div>


            <div style={{ textAlign: "right" }}>

              <p
                style={{
                  fontSize: "12px",
                  color: "#94a3b8",
                  margin: 0,
                }}
              >
                Last updated
              </p>

              <p
                style={{
                  fontSize: "14px",
                  color: "#334155",
                  margin: "4px 0 0",
                  fontWeight: "500",
                }}
              >
                Today, 10:32 AM
              </p>

            </div>

          </div>


          {/* =================================================
              KPI CARDS
          ================================================= */}

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
              gap: "20px",
              marginBottom: "24px",
            }}
          >

            {/* REVENUE */}

            <KpiCard
              icon={<TrendingUp size={21} />}
              iconBg="#eff6ff"
              iconColor="#2563eb"
              title="Total Revenue"
              value="₹15,20,000"
              growth="+12.5%"
            />


            {/* ORDERS */}

            <KpiCard
              icon={<BarChart3 size={21} />}
              iconBg="#f5f3ff"
              iconColor="#7c3aed"
              title="Total Orders"
              value="2,350"
            />


            {/* PROFIT */}

            <KpiCard
              icon={<TrendingUp size={21} />}
              iconBg="#f0fdf4"
              iconColor="#16a34a"
              title="Total Profit"
              value="₹4,20,000"
              growth="+8.4%"
            />


            {/* CUSTOMERS */}

            <KpiCard
              icon={<Users size={21} />}
              iconBg="#fff7ed"
              iconColor="#ea580c"
              title="Customers"
              value="980"
            />

          </div>


          {/* =================================================
              CHARTS
          ================================================= */}

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
              gap: "24px",
              marginBottom: "24px",
            }}
          >


            {/* SALES TREND */}

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
                    Sales Trend
                  </h2>

                  <p
                    style={{
                      fontSize: "13px",
                      color: "#64748b",
                      marginTop: "5px",
                    }}
                  >
                    Monthly revenue performance
                  </p>

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

                  <TrendingUp
                    size={18}
                    color="#16a34a"
                  />

                </div>

              </div>


              <div
                style={{
                  height: "300px",
                  width: "100%",
                }}
              >

                <Line
                  data={salesData}
                  options={options}
                />

              </div>

            </div>


            {/* TOP PRODUCTS */}

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
                    Top Products
                  </h2>

                  <p
                    style={{
                      fontSize: "13px",
                      color: "#64748b",
                      marginTop: "5px",
                    }}
                  >
                    Best performing products
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

                  <BarChart3
                    size={18}
                    color="#2563eb"
                  />

                </div>

              </div>


              <div
                style={{
                  height: "300px",
                  width: "100%",
                }}
              >

                <Bar
                  data={productData}
                  options={options}
                />

              </div>

            </div>

          </div>


          {/* =================================================
              BOTTOM CARDS
          ================================================= */}

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
              gap: "24px",
            }}
          >


            {/* AI INSIGHTS */}

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

                  <Sparkles
                    size={20}
                    color="#2563eb"
                  />

                </div>


                <div>

                  <h2
                    style={{
                      fontSize: "18px",
                      color: "#1e293b",
                      margin: 0,
                    }}
                  >
                    AI Insights
                  </h2>

                  <p
                    style={{
                      fontSize: "12px",
                      color: "#64748b",
                      marginTop: "3px",
                    }}
                  >
                    Key observations from your data
                  </p>

                </div>

              </div>


              <Insight text="Revenue has shown a positive growth trend during the last three months." />

              <Insight text="Product A is currently the strongest performing product." />

              <Insight text="Overall business performance is showing consistent growth." />

            </div>


            {/* DATA QUALITY */}

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
                    }}
                  >
                    Data Quality
                  </h2>

                  <p
                    style={{
                      fontSize: "12px",
                      color: "#64748b",
                      marginTop: "4px",
                    }}
                  >
                    Dataset health overview
                  </p>

                </div>


                <span
                  style={{
                    fontSize: "20px",
                    fontWeight: "700",
                    color: "#16a34a",
                  }}
                >
                  98.6%
                </span>

              </div>


              {/* PROGRESS */}

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
                    width: "98.6%",
                    height: "100%",
                    background: "#2563eb",
                    borderRadius: "20px",
                  }}
                />

              </div>


              {/* STATS */}

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(3, 1fr)",
                  gap: "15px",
                  marginTop: "25px",
                }}
              >

                <QualityStat
                  icon={<Database size={17} />}
                  color="#2563eb"
                  title="Valid"
                  value="4,957"
                />

                <QualityStat
                  icon={<AlertTriangle size={17} />}
                  color="#eab308"
                  title="Missing"
                  value="35"
                />

                <QualityStat
                  icon={<Copy size={17} />}
                  color="#ef4444"
                  title="Duplicate"
                  value="8"
                />

              </div>

            </div>

          </div>

        </main>

      </div>

    </div>
  );
}


/* =========================================================
   KPI CARD
========================================================= */

function KpiCard({
  icon,
  iconBg,
  iconColor,
  title,
  value,
  growth,
}) {
  return (
    <div
      style={{
        background: "#ffffff",
        border: "1px solid #e2e8f0",
        borderRadius: "16px",
        padding: "20px",
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
              color: "#16a34a",
            }}
          >
            {growth}
          </span>
        )}

      </div>


      <p
        style={{
          fontSize: "13px",
          color: "#64748b",
          marginTop: "18px",
          marginBottom: "4px",
        }}
      >
        {title}
      </p>


      <h2
        style={{
          fontSize: "25px",
          fontWeight: "700",
          color: "#1e293b",
          margin: 0,
        }}
      >
        {value}
      </h2>

    </div>
  );
}


/* =========================================================
   INSIGHT
========================================================= */

function Insight({ text }) {
  return (
    <div
      style={{
        background: "#f8fafc",
        borderRadius: "11px",
        padding: "13px 15px",
        marginBottom: "10px",
      }}
    >

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
   DATA QUALITY STAT
========================================================= */

function QualityStat({
  icon,
  color,
  title,
  value,
}) {
  return (
    <div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "7px",
          color,
        }}
      >

        {icon}

        <span
          style={{
            fontSize: "12px",
            color: "#64748b",
          }}
        >
          {title}
        </span>

      </div>


      <p
        style={{
          fontSize: "20px",
          fontWeight: "700",
          color: "#1e293b",
          margin: "5px 0 0",
        }}
      >
        {value}
      </p>

    </div>
  );
}