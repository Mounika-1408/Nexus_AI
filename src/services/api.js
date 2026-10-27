const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

function getAuthHeaders(extraHeaders = {}) {
  const token = localStorage.getItem("nexusaiToken");
  const headers = { ...extraHeaders };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

async function handleResponse(response) {
  if (response.status === 401) {
    localStorage.removeItem("nexusaiToken");
    localStorage.removeItem("nexusaiLoggedIn");
    localStorage.removeItem("nexusaiUser");
    if (window.location.pathname !== "/" && window.location.pathname !== "/signup") {
      window.location.href = "/";
    }
  }

  if (!response.ok) {
    let errorMessage = `HTTP error! Status: ${response.status}`;
    try {
      const errorData = await response.json();
      if (errorData && errorData.detail) {
        if (typeof errorData.detail === "string") {
          errorMessage = errorData.detail;
        } else if (Array.isArray(errorData.detail)) {
          errorMessage = errorData.detail.map((e) => e.msg || JSON.stringify(e)).join(", ");
        } else if (typeof errorData.detail === "object") {
          const detail = errorData.detail;
          if (detail.message) {
            errorMessage = detail.message;
            if (detail.missing_columns && Array.isArray(detail.missing_columns)) {
              errorMessage += ` (Missing: ${detail.missing_columns.join(", ")})`;
            }
          } else {
            errorMessage = JSON.stringify(detail);
          }
        }
      } else if (errorData && errorData.message) {
        errorMessage = errorData.message;
      }
    } catch {
      // Ignore JSON parse errors for non-JSON response body
    }
    throw new Error(errorMessage);
  }
  return await response.json();
}

/**
 * Authentication: Register a new user
 */
export async function registerUser({ name, email, password }) {
  const res = await fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password }),
  });
  const data = await handleResponse(res);
  if (data.token) {
    localStorage.setItem("nexusaiToken", data.token);
    localStorage.setItem("nexusaiLoggedIn", "true");
    localStorage.setItem("nexusaiUser", JSON.stringify(data.user));
  }
  return data;
}

/**
 * Authentication: Log in existing user
 */
export async function loginUser({ email, password }) {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await handleResponse(res);
  if (data.token) {
    localStorage.setItem("nexusaiToken", data.token);
    localStorage.setItem("nexusaiLoggedIn", "true");
    localStorage.setItem("nexusaiUser", JSON.stringify(data.user));
  }
  return data;
}

/**
 * Authentication: Log out user
 */
export function logoutUser() {
  localStorage.removeItem("nexusaiToken");
  localStorage.removeItem("nexusaiLoggedIn");
  localStorage.removeItem("nexusaiUser");
  window.location.href = "/";
}

/**
 * Fetch all uploaded datasets
 */
export async function fetchDatasets() {
  const res = await fetch(`${API_BASE_URL}/datasets/`, {
    headers: getAuthHeaders(),
  });
  return await handleResponse(res);
}

/**
 * Fetch dataset records by ID
 */
export async function fetchDatasetRecords(datasetId) {
  const res = await fetch(`${API_BASE_URL}/datasets/${datasetId}/records`, {
    headers: getAuthHeaders(),
  });
  return await handleResponse(res);
}

/**
 * Fetch dataset metadata/data quality metrics by ID
 */
export async function fetchDatasetMetadata(datasetId) {
  const res = await fetch(`${API_BASE_URL}/datasets/${datasetId}/metadata`, {
    headers: getAuthHeaders(),
  });
  return await handleResponse(res);
}

/**
 * Fetch dataset statistical summary by ID
 */
export async function fetchDatasetSummary(datasetId) {
  const res = await fetch(`${API_BASE_URL}/datasets/${datasetId}/summary`, {
    headers: getAuthHeaders(),
  });
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
    headers: getAuthHeaders(),
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
    headers: getAuthHeaders({
      "Content-Type": "application/json",
    }),
    body: JSON.stringify({
      tv: parseFloat(tv),
      radio: parseFloat(radio),
      newspaper: parseFloat(newspaper),
    }),
  });
  return await handleResponse(res);
}

/**
 * Fetch ML Model Info and Evaluation Metrics (A2 fix)
 */
export async function fetchModelInfo() {
  const res = await fetch(`${API_BASE_URL}/ai/predict/sales/model-info`, {
    headers: getAuthHeaders(),
  });
  return await handleResponse(res);
}

/**
 * Forecast future financial revenue based on uploaded dataset records
 */
export async function forecastRevenue({ dataset_id, horizon_days = 30, anchor_date = null }) {
  const payload = {
    dataset_id: parseInt(dataset_id, 10),
    horizon_days: parseInt(horizon_days, 10),
  };
  if (anchor_date) {
    payload.anchor_date = anchor_date;
  }

  const res = await fetch(`${API_BASE_URL}/ai/forecast/revenue`, {
    method: "POST",
    headers: getAuthHeaders({
      "Content-Type": "application/json",
    }),
    body: JSON.stringify(payload),
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
    headers: getAuthHeaders({
      "Content-Type": "application/json",
    }),
    body: JSON.stringify(payload),
  });
  return await handleResponse(res);
}

/**
 * Reprocess an existing dataset by ID
 */
export async function reprocessDataset(datasetId) {
  const res = await fetch(`${API_BASE_URL}/datasets/${datasetId}/reprocess`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  return await handleResponse(res);
}

