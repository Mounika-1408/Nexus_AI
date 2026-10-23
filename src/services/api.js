const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function handleResponse(response) {
  if (!response.ok) {
    let errorMessage = `HTTP error! Status: ${response.status}`;
    try {
      const errorData = await response.json();
      if (errorData && errorData.detail) {
        if (typeof errorData.detail === "string") {
          errorMessage = errorData.detail;
        } else if (Array.isArray(errorData.detail)) {
          errorMessage = errorData.detail.map((e) => e.msg || JSON.stringify(e)).join(", ");
        }
      }
    } catch {
      // Ignore JSON parse errors for non-JSON response body
    }
    throw new Error(errorMessage);
  }
  return await response.json();
}

/**
 * Fetch all uploaded datasets
 */
export async function fetchDatasets() {
  const res = await fetch(`${API_BASE_URL}/datasets/`);
  return await handleResponse(res);
}

/**
 * Fetch dataset records by ID
 */
export async function fetchDatasetRecords(datasetId) {
  const res = await fetch(`${API_BASE_URL}/datasets/${datasetId}/records`);
  return await handleResponse(res);
}

/**
 * Fetch dataset metadata/data quality metrics by ID
 */
export async function fetchDatasetMetadata(datasetId) {
  const res = await fetch(`${API_BASE_URL}/datasets/${datasetId}/metadata`);
  return await handleResponse(res);
}

/**
 * Fetch dataset statistical summary by ID
 */
export async function fetchDatasetSummary(datasetId) {
  const res = await fetch(`${API_BASE_URL}/datasets/${datasetId}/summary`);
  return await handleResponse(res);
}

/**
 * Upload a dataset CSV/XLSX file to POST /upload
 */
export async function uploadDataset(file) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE_URL}/upload`, {
    method: "POST",
    body: formData,
  });
  return await handleResponse(res);
}

/**
 * Predict Sales based on TV, Radio, and Newspaper advertising budgets
 */
export async function predictSales({ tv, radio, newspaper }) {
  const res = await fetch(`${API_BASE_URL}/ai/predict/sales`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      tv: parseFloat(tv),
      radio: parseFloat(radio),
      newspaper: parseFloat(newspaper),
    }),
  });
  return await handleResponse(res);
}

/**
 * Forecast future financial revenue based on uploaded dataset records
 */
export async function forecastRevenue({ dataset_id, horizon_days = 30 }) {
  const res = await fetch(`${API_BASE_URL}/ai/forecast/revenue`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      dataset_id: parseInt(dataset_id, 10),
      horizon_days: parseInt(horizon_days, 10),
    }),
  });
  return await handleResponse(res);
}

/**
 * Ask natural language questions via Text-to-SQL Chat API
 */
export async function sendChatMessage({ message, dataset_id = null }) {
  const payload = { message };
  if (dataset_id !== null && dataset_id !== undefined && dataset_id !== "") {
    payload.dataset_id = parseInt(dataset_id, 10);
  }

  const res = await fetch(`${API_BASE_URL}/ai/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  return await handleResponse(res);
}
