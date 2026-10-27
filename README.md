# NexusAI - AI-Powered Business & Financial Analytics

NexusAI is a full-stack financial analytics platform combining automated ETL data ingestion, multi-currency normalization, Holt Damped Trend revenue forecasting, machine learning sales prediction, natural-language Text-to-SQL querying, and a voice assistant console.

---

## Architecture Overview

- **Frontend**: React 19 + Vite + React Router + Chart.js (`src/`)
- **Backend**: FastAPI + SQLAlchemy 2.0 + Pydantic v2 + Pandas (`backend/app/`)
- **Machine Learning**: Scikit-Learn Regression Pipeline (`ai/prediction/`)
- **Database**: PostgreSQL / Supabase (`DATABASE_URL`) with isolated SQLite for automated testing

---

## Quickstart Guide

### 1. Backend Setup

1. Navigate to the backend directory and activate your Python virtual environment:
   ```bash
   cd backend
   ```
2. Configure your environment variables in `backend/.env` (see `backend/.env.example` for reference):
   ```env
   DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/postgres
   JWT_SECRET=nexusai_jwt_secret_change_in_production_key_2026
   ENVIRONMENT=development
   FRONTEND_URL=http://localhost:5173
   ```
3. Install required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the FastAPI backend server:
   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```

### 2. Frontend Setup

1. Install Node dependencies:
   ```bash
   npm install
   ```
2. Start the Vite development server:
   ```bash
   npm run dev
   ```
3. Open `http://localhost:5173` in your browser.

---

## Running Automated Tests

Tests run against an isolated SQLite database without modifying live Supabase data:
```bash
pytest backend/tests/ -v
```

---

## Platform Features

1. **Enterprise Authentication**: Secure user registration and login with bcrypt password hashing and JWT access tokens.
2. **Robust Multi-Currency ETL**:
   - Ingests CSV and Excel files.
   - Converts multi-currency transactions (USD, EUR, GBP, INR) to base USD currency.
   - Cleans dirty records, removes duplicates, and filters out cancelled/refunded payments.
3. **Optimized Holt Damped Revenue Forecasting**:
   - Dynamic parameter optimization (grid search for $\alpha, \beta, \phi$) to eliminate hypersensitivity to trailing spikes.
   - Trailing-zero safeguard preventing artificial $\$0$ / $-100\%$ forecast collapses.
   - Honest held-out evaluation reporting WAPE and sMAPE.
4. **Advertising ML Sales Prediction**:
   - Compares Linear Regression, Ridge, Random Forest, and Gradient Boosting.
   - Reports 5-fold cross-validation and test metrics from dynamic `metrics.json`.
   - Domain extrapolation warning for out-of-distribution input budgets.
5. **Interactive Text-to-SQL Chat**:
   - Parameterized SQL execution restricted to allowed financial tables.
   - Whitelist protection blocking access to system tables, `users`, and SQL injection functions.
6. **Live Voice Assistant Console**:
   - Real-time speech-to-text with Web Speech API.
   - Live spoken answer playback with Web SpeechSynthesis and audio mute toggle.

---

## Demo Walkthrough

A synthetic demo dataset is provided in `uploads/synthetic_demo_financial_data.csv`:
1. Register/Login at `http://localhost:5173`.
2. Go to **Upload Dataset** and select `uploads/synthetic_demo_financial_data.csv`.
3. View the clean rows and Data Quality Score in the **Dashboard**.
4. Explore multi-currency charts and totals in **Analytics**.
5. Query natural language metrics in **AI Chat** and **Voice Assistant**.
6. Run 30-day and 90-day projections in **Prediction** (Revenue Forecast & Sales Prediction).
