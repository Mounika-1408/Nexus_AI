import "./../styles/RecentUploads.css";

function RecentUploads({ datasets = [], loading = false }) {
  return (
    <div className="recent-card">
      <h3>Recent Dataset Uploads</h3>

      <div className="upload-list">
        {loading ? (
          <p style={{ color: "#64748b", fontSize: "0.875rem" }}>Loading datasets from server...</p>
        ) : datasets.length === 0 ? (
          <p style={{ color: "#64748b", fontSize: "0.875rem" }}>No datasets uploaded yet.</p>
        ) : (
          datasets.slice(0, 5).map((ds) => (
            <div className="upload-item" key={ds.id}>
              <div className="file-icon">📄</div>
              <div>
                <p className="file-name">
                  {ds.file_name} <span style={{ fontSize: "0.75rem", color: "#64748b" }}>(ID: #{ds.id})</span>
                </p>
                <span style={{ fontSize: "0.75rem", color: "#16a34a", fontWeight: "600" }}>
                  Status: {ds.status || "Completed"} • Type: {ds.file_type.toUpperCase()}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default RecentUploads;