import "../styles/AIInsights.css";

function AIInsights({ summary, metadata }) {
  const profitMargin =
    summary && summary.total_revenue > 0
      ? ((summary.total_profit / summary.total_revenue) * 100).toFixed(1)
      : null;

  return (
    <div className="ai-card">
      <h3>✦ Automated AI Insights</h3>

      <div className="insight-list">
        <div className="insight-item">
          <span className="insight-icon">📈</span>
          <div>
            <p>
              {summary && summary.total_profit !== undefined
                ? `Net profit recorded at $${summary.total_profit.toLocaleString()} with a ${profitMargin}% profit margin.`
                : "Continuous ETL processing monitors real-time revenue and expenditure trends."}
            </p>
          </div>
        </div>

        <div className="insight-item">
          <span className="insight-icon">🛡️</span>
          <div>
            <p>
              {metadata && metadata.data_quality_score !== undefined
                ? `Automated data quality score is ${metadata.data_quality_score}%. ${metadata.duplicates_removed || 0} duplicates and ${metadata.invalid_rows || 0} invalid entries cleaned.`
                : "Automated schema and data validation pipelines ensure clean transaction records."}
            </p>
          </div>
        </div>

        <div className="insight-item">
          <span className="insight-icon">💡</span>
          <div>
            <p>
              Natural language Text-to-SQL is ready to answer specific queries across your ingested datasets.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AIInsights;