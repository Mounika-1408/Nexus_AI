import { useState } from "react";

import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";

import "../styles/Upload.css";

function Upload() {
  const [file, setFile] = useState(null);

  function handleFileChange(e) {
    if (e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  }

  return (
    <div className="dashboard">

      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <div className="dashboard-content">

        {/* Navbar */}
        <Navbar />

        {/* Upload Page */}
        <div className="upload-page">

          {/* Header */}
          <div className="page-header">

            <h1>Upload Dataset</h1>

            <p>
              Upload CSV, Excel or JSON datasets for AI-powered analytics.
            </p>

          </div>


          {/* Upload Card */}
          <div className="upload-card">

            <div className="upload-area">

              <div className="upload-icon">
                📂
              </div>

              <h2>
                Drag & Drop Your Dataset
              </h2>

              <p>
                or choose a file from your computer
              </p>

              <input
                type="file"
                accept=".csv,.xlsx,.xls,.json"
                onChange={handleFileChange}
              />

            </div>


            {/* File Information */}
            {file && (

              <div className="file-details">

                <h3>
                  Dataset Information
                </h3>


                <div className="detail-row">

                  <span>
                    File Name
                  </span>

                  <strong>
                    {file.name}
                  </strong>

                </div>


                <div className="detail-row">

                  <span>
                    File Size
                  </span>

                  <strong>
                    {(file.size / 1024).toFixed(2)} KB
                  </strong>

                </div>


                <div className="detail-row">

                  <span>
                    File Type
                  </span>

                  <strong>
                    {file.type || "Unknown"}
                  </strong>

                </div>


                <button className="upload-btn">
                  Upload Dataset
                </button>

              </div>

            )}

          </div>


          {/* Upload History */}
          <div className="history-card">

            <h2>
              Recent Uploads
            </h2>


            <table>

              <thead>

                <tr>
                  <th>Dataset</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Date</th>
                </tr>

              </thead>


              <tbody>

                <tr>
                  <td>sales_july.csv</td>
                  <td>CSV</td>
                  <td className="success">
                    Completed
                  </td>
                  <td>Today</td>
                </tr>


                <tr>
                  <td>finance.xlsx</td>
                  <td>Excel</td>
                  <td className="success">
                    Completed
                  </td>
                  <td>Yesterday</td>
                </tr>


                <tr>
                  <td>inventory.csv</td>
                  <td>CSV</td>
                  <td className="pending">
                    Processing
                  </td>
                  <td>2 days ago</td>
                </tr>

              </tbody>

            </table>

          </div>

        </div>

      </div>

    </div>
  );
}

export default Upload;