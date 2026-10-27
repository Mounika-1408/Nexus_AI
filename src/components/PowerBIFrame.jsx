import { useState } from "react";
import { ExternalLink, ShieldCheck, RefreshCw, BarChart2 } from "lucide-react";
import "../styles/PowerBIFrame.css";

const POWER_BI_REPORT_URL =
  "https://app.powerbi.com/reportEmbed?reportId=babba002-ed7e-4e37-b7ce-875ad03bd80a&autoAuth=true&ctid=7b8d4885-765a-4299-9a92-4edb30779085";

export default function PowerBIFrame() {
  const [isLoading, setIsLoading] = useState(true);

  return (
    <section className="powerbi-container" aria-label="Microsoft Power BI Analytics Dashboard">
      <div className="powerbi-header">
        <div className="powerbi-header-left">
          <div className="powerbi-icon-wrap">
            <BarChart2 size={22} className="powerbi-icon" />
          </div>
          <div>
            <div className="powerbi-title-row">
              <h2>Business Analytics Dashboard</h2>
              <span className="powerbi-badge">
                <ShieldCheck size={13} />
                Secure Power BI Embed
              </span>
            </div>
            <p>Finance insights powered by Microsoft Power BI</p>
          </div>
        </div>

        <div className="powerbi-actions">
          <a
            href={POWER_BI_REPORT_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="powerbi-external-btn"
            title="Open report in Microsoft Power BI Service"
          >
            <span>Open in Power BI</span>
            <ExternalLink size={15} />
          </a>
        </div>
      </div>

      <div className="powerbi-notice">
        <p>
          <strong>Enterprise Authentication:</strong> This dashboard is securely embedded from your Microsoft Power BI tenant. If a Microsoft login prompt appears, sign in using your authorized organizational credentials to view the live report.
        </p>
      </div>

      <div className="powerbi-report">
        {isLoading && (
          <div className="powerbi-loading-overlay">
            <RefreshCw size={26} className="powerbi-spinner" />
            <span>Connecting to Microsoft Power BI...</span>
          </div>
        )}
        <iframe
          title="NexusAI Finance Report"
          src={POWER_BI_REPORT_URL}
          width="100%"
          height="650"
          style={{ border: "none" }}
          allowFullScreen
          onLoad={() => setIsLoading(false)}
        />
      </div>
    </section>
  );
}