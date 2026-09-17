import React, { useState } from "react";
import Sidebar from "../components/Sidebar";
import "../styles/Prediction.css";

function Prediction() {
  const [predictionType, setPredictionType] = useState("Sales Forecast");
  const [forecastPeriod, setForecastPeriod] = useState("7 Days");
  const [isLoading, setIsLoading] = useState(false);
  const [showResult, setShowResult] = useState(false);

  const generatePrediction = () => {
    setIsLoading(true);
    setShowResult(false);

    // Temporary demo prediction.
    // Later this will be replaced by your backend/ML API.
    setTimeout(() => {
      setIsLoading(false);
      setShowResult(true);
    }, 1200);
  };

  return (
    <div className="prediction-page">
      <Sidebar />

      <main className="prediction-main">

        {/* Header */}
        <div className="prediction-header">
          <div>
            <h1>Prediction</h1>
            <p>
              Use your business data to generate future predictions
            </p>
          </div>
        </div>

        {/* Prediction Setup */}
        <div className="prediction-card">

          <div className="card-title">
            <div className="prediction-symbol">✦</div>

            <div>
              <h2>Generate Prediction</h2>
              <p>
                Configure the prediction you want to generate
              </p>
            </div>
          </div>

          <div className="prediction-form">

            {/* Dataset */}
            <div className="form-group">
              <label>Dataset</label>

              <select>
                <option>Analytics dataset</option>
                <option>sales_data.csv</option>
                <option>business_data.xlsx</option>
              </select>

              <small>
                Select the dataset you want to analyze
              </small>
            </div>

            {/* Prediction Type */}
            <div className="form-group">
              <label>Prediction Type</label>

              <select
                value={predictionType}
                onChange={(e) => setPredictionType(e.target.value)}
              >
                <option>Sales Forecast</option>
                <option>Revenue Forecast</option>
                <option>Demand Forecast</option>
                <option>Customer Forecast</option>
              </select>
            </div>

            {/* Forecast Period */}
            <div className="form-group">
              <label>Forecast Period</label>

              <select
                value={forecastPeriod}
                onChange={(e) => setForecastPeriod(e.target.value)}
              >
                <option>7 Days</option>
                <option>14 Days</option>
                <option>30 Days</option>
                <option>90 Days</option>
              </select>
            </div>

          </div>

          <button
            className="generate-button"
            onClick={generatePrediction}
            disabled={isLoading}
          >
            {isLoading ? "Generating..." : "Generate Prediction"}
            {!isLoading && <span>→</span>}
          </button>

        </div>

        {/* Results */}
        {showResult && (
          <div className="prediction-results">

            <div className="results-header">
              <div>
                <h2>Prediction Results</h2>
                <p>
                  Based on the selected dataset and prediction settings
                </p>
              </div>

              <div className="prediction-status">
                <span></span>
                Prediction Generated
              </div>
            </div>

            {/* KPI Cards */}
            <div className="prediction-kpis">

              <div className="prediction-kpi">
                <p>Forecasted Sales</p>
                <h3>₹3,42,500</h3>
                <span className="positive">↑ 12.4%</span>
              </div>

              <div className="prediction-kpi">
                <p>Expected Growth</p>
                <h3>12.4%</h3>
                <span className="positive">
                  Positive trend
                </span>
              </div>

              <div className="prediction-kpi">
                <p>Forecast Period</p>
                <h3>{forecastPeriod}</h3>
                <span>
                  Future estimate
                </span>
              </div>

            </div>

            {/* Chart */}
            <div className="forecast-card">

              <div className="forecast-header">
                <div>
                  <h3>Sales Forecast</h3>
                  <p>
                    Historical sales and predicted values
                  </p>
                </div>
              </div>

              <div className="forecast-chart">

                <div className="chart-y-axis">
                  <span>₹40K</span>
                  <span>₹30K</span>
                  <span>₹20K</span>
                  <span>₹10K</span>
                  <span>₹0</span>
                </div>

                <div className="chart-area">

                  <div className="grid-line line-1"></div>
                  <div className="grid-line line-2"></div>
                  <div className="grid-line line-3"></div>
                  <div className="grid-line line-4"></div>
                  <div className="grid-line line-5"></div>

                  <div className="chart-bars">

                    <div className="bar" style={{ height: "35%" }}>
                      <span>Jan</span>
                    </div>

                    <div className="bar" style={{ height: "48%" }}>
                      <span>Feb</span>
                    </div>

                    <div className="bar" style={{ height: "40%" }}>
                      <span>Mar</span>
                    </div>

                    <div className="bar" style={{ height: "58%" }}>
                      <span>Apr</span>
                    </div>

                    <div className="bar" style={{ height: "72%" }}>
                      <span>May</span>
                    </div>

                    <div className="bar" style={{ height: "82%" }}>
                      <span>Jun</span>
                    </div>

                    <div className="bar predicted" style={{ height: "91%" }}>
                      <span>Jul</span>
                    </div>

                  </div>

                </div>

              </div>

              <div className="chart-legend">
                <div>
                  <span className="legend-box historical"></span>
                  Historical
                </div>

                <div>
                  <span className="legend-box forecast"></span>
                  Forecast
                </div>
              </div>

            </div>

            {/* AI Insight */}
            <div className="prediction-insight">

              <div className="insight-icon">
                ✦
              </div>

              <div>
                <h3>Prediction Insight</h3>

                <p>
                  Based on the current trend, sales are expected
                  to continue increasing during the forecast period.
                  The predicted growth is approximately 12.4%.
                </p>
              </div>

            </div>

          </div>
        )}

      </main>
    </div>
  );
}

export default Prediction;