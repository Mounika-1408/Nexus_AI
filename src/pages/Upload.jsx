import { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";
import { uploadDataset, fetchDatasets } from "../services/api";

import "../styles/Upload.css";

function Upload() {
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const [uploadError, setUploadError] = useState(null);

  const [recentDatasets, setRecentDatasets] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(true);

  useEffect(() => {
    loadUploadHistory();
  }, []);

  async function loadUploadHistory() {
    try {
      setLoadingHistory(true);
      const data = await fetchDatasets();
      setRecentDatasets(data);
    } catch (err) {
      console.error("Failed to load upload history:", err);
    } finally {
      setLoadingHistory(false);
    }
  }

  function handleFileChange(e) {
    if (e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setUploadSuccess(null);
      setUploadError(null);
    }
  }

  async function handleUploadSubmit(e) {
    e.preventDefault();
    if (!file) return;

    try {
      setIsUploading(true);
      setUploadError(null);
      setUploadSuccess(null);

      const result = await uploadDataset(file);

      setUploadSuccess({
        dataset_id: result.dataset_id,
        file_name: result.file_name || file.name,
        message: result.message || "File uploaded and processed successfully!",
        status: result.status || "Completed",
      });

      setFile(null);
      // Refresh upload history table
      await loadUploadHistory();
    } catch (err) {
      setUploadError(err.message || "An error occurred during dataset upload.");
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div className="dashboard">
      <Sidebar />

      <div className="dashboard-content">
        <Navbar />

        <div className="upload-page">
          <div className="page-header">
            <h1>Upload Dataset</h1>
            <p>
              Upload CSV or Excel datasets for automated ETL, data cleaning, metadata calculation, and AI analytics.
            </p>
          </div>

          {/* Upload Status Banners */}
          {uploadSuccess && (
            <div style={{ padding: "16px", background: "#f0fdf4", border: "1px solid #bbf7d0", color: "#15803d", borderRadius: "10px", marginBottom: "20px" }}>
              <h4 style={{ margin: "0 0 6px 0", fontSize: "1rem" }}>✅ Upload Successful!</h4>
              <p style={{ margin: 0, fontSize: "0.9rem" }}>
                Dataset <strong>#{uploadSuccess.dataset_id}</strong> (<em>{uploadSuccess.file_name}</em>) uploaded successfully.
                <br />
                ETL Processing Status: <strong>{uploadSuccess.status}</strong>
              </p>
            </div>
          )}

          {uploadError && (
            <div style={{ padding: "16px", background: "#fef2f2", border: "1px solid #fecaca", color: "#b91c1c", borderRadius: "10px", marginBottom: "20px" }}>
              <h4 style={{ margin: "0 0 6px 0", fontSize: "1rem" }}>⚠️ Upload Failed</h4>
              <p style={{ margin: 0, fontSize: "0.9rem" }}>{uploadError}</p>
            </div>
          )}

          {/* Upload Card */}
          <div className="upload-card">
            <form onSubmit={handleUploadSubmit}>
              <div className="upload-area" style={{ border: "2px dashed #cbd5e1", borderRadius: "12px", padding: "32px", textAlign: "center", cursor: "pointer", background: "#f8fafc" }}>
                <div className="upload-icon" style={{ fontSize: "2.5rem", marginBottom: "12px" }}>📂</div>
                <h2 style={{ fontSize: "1.25rem", color: "#1e293b", marginBottom: "6px" }}>Drag & Drop Your Dataset</h2>
                <p style={{ fontSize: "0.875rem", color: "#64748b", marginBottom: "16px" }}>Select a CSV or Excel file (.csv, .xlsx, .xls) from your computer</p>

                <input
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={handleFileChange}
                  style={{ margin: "0 auto", display: "inline-block" }}
                />
              </div>

              {/* File Information */}
              {file && (
                <div className="file-details" style={{ marginTop: "20px", padding: "16px", background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "10px" }}>
                  <h3 style={{ fontSize: "1rem", color: "#0f172a", marginBottom: "12px" }}>Dataset Information</h3>

                  <div className="detail-row" style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                    <span>File Name</span>
                    <strong>{file.name}</strong>
                  </div>

                  <div className="detail-row" style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                    <span>File Size</span>
                    <strong>{(file.size / 1024).toFixed(2)} KB</strong>
                  </div>

                  <div className="detail-row" style={{ display: "flex", justifyContent: "space-between", marginBottom: "16px" }}>
                    <span>File Type</span>
                    <strong>{file.name.split(".").pop().toUpperCase()}</strong>
                  </div>

                  <button
                    type="submit"
                    className="upload-btn"
                    disabled={isUploading}
                    style={{
                      width: "100%",
                      padding: "12px",
                      background: isUploading ? "#94a3b8" : "#2563eb",
                      color: "#ffffff",
                      border: "none",
                      borderRadius: "8px",
                      fontWeight: "600",
                      cursor: isUploading ? "not-allowed" : "pointer"
                    }}
                  >
                    {isUploading ? "Uploading & Running Automated ETL..." : "Upload & Process Dataset"}
                  </button>
                </div>
              )}
            </form>
          </div>

          {/* Upload History Table */}
          <div className="history-card" style={{ marginTop: "32px", background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "12px", padding: "20px" }}>
            <h2 style={{ fontSize: "1.25rem", color: "#0f172a", marginBottom: "16px" }}>Recent Dataset Uploads & ETL History</h2>

            {loadingHistory ? (
              <p style={{ color: "#64748b" }}>Loading datasets from server...</p>
            ) : recentDatasets.length === 0 ? (
              <p style={{ color: "#64748b" }}>No datasets found. Upload your first dataset above.</p>
            ) : (
              <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
                <thead>
                  <tr style={{ borderBottom: "2px solid #e2e8f0", color: "#64748b", fontSize: "0.875rem" }}>
                    <th style={{ padding: "10px" }}>Dataset ID</th>
                    <th style={{ padding: "10px" }}>File Name</th>
                    <th style={{ padding: "10px" }}>Type</th>
                    <th style={{ padding: "10px" }}>ETL Status</th>
                  </tr>
                </thead>
                <tbody>
                  {recentDatasets.map((ds) => (
                    <tr key={ds.id} style={{ borderBottom: "1px solid #f1f5f9" }}>
                      <td style={{ padding: "12px 10px", fontWeight: "600" }}>#{ds.id}</td>
                      <td style={{ padding: "12px 10px" }}>{ds.file_name}</td>
                      <td style={{ padding: "12px 10px" }}>
                        <span style={{ padding: "4px 8px", background: "#f1f5f9", borderRadius: "4px", fontSize: "0.75rem", fontWeight: "600" }}>
                          {ds.file_type.toUpperCase()}
                        </span>
                      </td>
                      <td style={{ padding: "12px 10px" }}>
                        <span style={{ color: "#16a34a", fontWeight: "600", fontSize: "0.875rem" }}>
                          ● {ds.status || "Completed"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Upload;