import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd
import numpy as np
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models.dataset import Dataset
from app.models.finance_record import FinanceRecord


from app.services.currency_service import BASE_CURRENCY


def detect_dataset_currency(dataset: Dataset) -> str:
    """
    All aggregated finance records are stored normalized in Base Currency (USD).
    """
    return BASE_CURRENCY


def forecast_revenue_service(dataset_id: int, horizon_days: int = 30) -> Dict[str, Any]:
    """
    Generates a defensible financial revenue forecast using Holt's Damped Linear Trend
    exponential smoothing applied to real historical date and revenue records.
    """
    # 1. Validate Horizon
    allowed_horizons = [7, 30, 90]
    if horizon_days not in allowed_horizons:
        raise HTTPException(
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            detail=f"Invalid forecast horizon ({horizon_days} days). Supported horizons are 7, 30, or 90 days."
        )

    # 2. Database Fetch
    db: Session = SessionLocal()
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset #{dataset_id} does not exist."
            )

        records = (
            db.query(FinanceRecord)
            .filter(FinanceRecord.dataset_id == dataset_id)
            .all()
        )

        if not records or len(records) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dataset #{dataset_id} contains no financial transaction records."
            )

        # 3. Clean and Parse Records
        raw_data = []
        for r in records:
            rev_val = r.revenue
            if rev_val is not None:
                try:
                    rev_float = float(rev_val)
                    if not np.isnan(rev_float) and rev_float >= 0:
                        raw_data.append({"date": str(r.date).strip(), "revenue": rev_float})
                except (ValueError, TypeError):
                    continue

        if len(raw_data) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dataset #{dataset_id} contains no valid non-negative revenue entries."
            )

        df = pd.DataFrame(raw_data)
        df["parsed_date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["parsed_date"])

        if len(df) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dataset #{dataset_id} does not contain any valid parseable date values."
            )

        # 4. Aggregate daily revenue & validate sufficiency
        daily_agg = df.groupby(df["parsed_date"].dt.strftime("%Y-%m-%d"))["revenue"].sum().sort_index()
        distinct_daily_count = len(daily_agg)

        MIN_REQUIRED_OBSERVATIONS = 5
        if distinct_daily_count < MIN_REQUIRED_OBSERVATIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Insufficient historical observations. Dataset #{dataset_id} contains only "
                    f"{distinct_daily_count} distinct daily observation(s). A minimum of "
                    f"{MIN_REQUIRED_OBSERVATIONS} distinct daily records is required to generate a baseline forecast."
                )
            )

        # 5. Complete calendar range & impute missing calendar days with zero
        start_date = pd.to_datetime(daily_agg.index.min())
        end_date = pd.to_datetime(daily_agg.index.max())
        full_date_range = pd.date_range(start=start_date, end=end_date, freq="D")
        
        # Convert daily_agg index to DateTimeIndex for reindexing
        daily_series_dt = daily_agg.copy()
        daily_series_dt.index = pd.to_datetime(daily_series_dt.index)
        daily_full = daily_series_dt.reindex(full_date_range, fill_value=0.0)

        missing_days_count = len(full_date_range) - distinct_daily_count
        y = daily_full.values.astype(float)
        T = len(y)

        # 6. Fit Holt's Damped Linear Trend Model
        # Level: L_t = alpha * y_t + (1 - alpha) * (L_{t-1} + phi * b_{t-1})
        # Trend: b_t = beta * (L_t - L_{t-1}) + (1 - beta) * phi * b_{t-1}
        # Forecast: y_{T+h} = L_T + sum_{i=1}^h (phi^i) * b_T
        alpha = 0.30
        beta = 0.10
        phi = 0.90  # Damping factor to avoid unrealistic growth for 30/90 days

        L = np.zeros(T)
        b = np.zeros(T)
        L[0] = max(0.0, y[0])
        # Neutral initial trend prior (b_0 = 0) avoids volatile first-difference noise
        b[0] = 0.0

        for t in range(1, T):
            prev_forecast = L[t - 1] + phi * b[t - 1]
            L[t] = max(0.0, alpha * y[t] + (1.0 - alpha) * prev_forecast)
            b[t] = beta * (L[t] - L[t - 1]) + (1.0 - beta) * phi * b[t - 1]

        # Calculate in-sample residual standard deviation for confidence intervals
        in_sample_preds = np.zeros(T)
        in_sample_preds[0] = y[0]
        for t in range(1, T):
            in_sample_preds[t] = max(0.0, L[t - 1] + phi * b[t - 1])

        residuals = y[1:] - in_sample_preds[1:] if T > 1 else np.array([0.0])
        std_error = float(np.std(residuals)) if len(residuals) > 0 else 1.0
        if std_error == 0.0:
            std_error = float(np.mean(y) * 0.1) or 1.0

        # 7. Generate Horizon Forecasts & Confidence Bounds (80% level: z = 1.28)
        forecast_points = []
        for h in range(1, horizon_days + 1):
            damping_sum = sum(phi ** i for i in range(1, h + 1))
            point_forecast = max(0.0, float(L[-1] + damping_sum * b[-1]))
            
            # Uncertainty expands with horizon
            step_std = std_error * np.sqrt(1.0 + (h - 1) * (alpha ** 2))
            lower_bound = max(0.0, float(point_forecast - 1.28 * step_std))
            upper_bound = float(point_forecast + 1.28 * step_std)

            fc_date = end_date + pd.Timedelta(days=h)
            forecast_points.append({
                "date": fc_date.strftime("%Y-%m-%d"),
                "forecast_revenue": round(point_forecast, 2),
                "lower_bound": round(lower_bound, 2),
                "upper_bound": round(upper_bound, 2),
            })

        # 8. Out-of-Sample Backtesting Evaluation (Honest evaluation on held-out split)
        # Evaluated only when T >= 7 daily historical points exist.
        evaluation_meta = None
        if T >= 7:
            test_size = max(2, min(5, int(T * 0.25)))
            train_T = T - test_size

            # Fit on training split
            L_tr = np.zeros(train_T)
            b_tr = np.zeros(train_T)
            L_tr[0] = max(0.0, y[0])
            b_tr[0] = 0.0

            for t in range(1, train_T):
                p_fc = L_tr[t - 1] + phi * b_tr[t - 1]
                L_tr[t] = max(0.0, alpha * y[t] + (1.0 - alpha) * p_fc)
                b_tr[t] = beta * (L_tr[t] - L_tr[t - 1]) + (1.0 - beta) * phi * b_tr[t - 1]

            # Forecast across test split
            test_actuals = y[train_T:]
            test_preds = []
            for h in range(1, test_size + 1):
                d_sum = sum(phi ** i for i in range(1, h + 1))
                test_preds.append(max(0.0, float(L_tr[-1] + d_sum * b_tr[-1])))
            test_preds = np.array(test_preds)

            mae = float(np.mean(np.abs(test_actuals - test_preds)))
            rmse = float(np.sqrt(np.mean((test_actuals - test_preds) ** 2)))
            
            # Avoid divide-by-zero for MAPE
            denom = np.where(test_actuals == 0, 1.0, test_actuals)
            mape = float(np.mean(np.abs(test_actuals - test_preds) / denom) * 100.0)

            evaluation_meta = {
                "evaluated_on_held_out": True,
                "test_days_held_out": test_size,
                "mae": round(mae, 2),
                "rmse": round(rmse, 2),
                "mape_percent": round(mape, 1),
                "notes": f"Model evaluated on the most recent {test_size} held-out historical days."
            }
        else:
            evaluation_meta = {
                "evaluated_on_held_out": False,
                "test_days_held_out": 0,
                "mae": None,
                "rmse": None,
                "mape_percent": None,
                "notes": (
                    "Historical data size is below the minimum threshold (>= 7 daily observations) "
                    "required for an out-of-sample test split. Accuracy evaluation is withheld to prevent "
                    "unverified claims."
                )
            }

        # 9. Format Historical Observations
        historical_points = [
            {"date": d.strftime("%Y-%m-%d"), "revenue": round(float(val), 2)}
            for d, val in zip(full_date_range, y)
        ]

        # 10. Summary Calculations
        total_hist_rev = round(float(np.sum(y)), 2)
        avg_hist_rev = round(float(np.mean(y)), 2)
        fc_values = [p["forecast_revenue"] for p in forecast_points]
        total_fc_rev = round(float(np.sum(fc_values)), 2)
        avg_fc_rev = round(total_fc_rev / horizon_days, 2)

        change_pct = 0.0
        if avg_hist_rev > 0:
            change_pct = round(((avg_fc_rev - avg_hist_rev) / avg_hist_rev) * 100.0, 1)

        currency = detect_dataset_currency(dataset)

        is_limited_sample = T < 30
        interval_label = "80% (Approximate)" if is_limited_sample else "80%"
        uncertainty_note = (
            f"Approximate uncertainty estimate: Historical baseline is limited ({T} daily observation(s)). "
            "Prediction interval bounds reflect in-sample residual spread and should be treated as an approximate "
            "heuristic rather than a rigorous asymptotic parametric interval."
        ) if is_limited_sample else "Standard parametric prediction interval based on residual variance."

        # Assumptions and limitations
        assumptions = [
            "Transactions aggregated into daily calendar revenue totals.",
            f"Missing calendar dates between {start_date.strftime('%Y-%m-%d')} and {end_date.strftime('%Y-%m-%d')} "
            f"imputed with 0.0 ({missing_days_count} days imputed).",
            "Values normalized to Base Currency (USD) using explicit reference exchange rates.",
            "Non-negative constraint enforced: forecast revenue cannot drop below zero.",
            f"Holt's linear trend with damping (phi={phi}) applied to prevent compounding growth over time.",
            f"Confidence interval bounds computed at {interval_label} level (z=1.28) using in-sample residual standard deviation"
            f"{' (approximate due to limited sample size of ' + str(T) + ' daily observations)' if is_limited_sample else ''}."
        ]

        limitations = [
            "Does not incorporate external market demand shocks, price changes, or competitor events.",
            "Seasonal adjustments (e.g. quarterly or annual seasonality) require at least 1-2 years of continuous records.",
            "Non-negative constraint behavior: when projected daily trend reaches zero, further horizon extensions contribute zero marginal revenue, resulting in equal cumulative totals across longer horizons."
        ]
        if is_limited_sample:
            limitations.insert(
                0,
                f"Statistical limitation: Short historical series ({T} daily observation(s)) creates wide, approximate "
                f"prediction intervals that are sensitive to individual outlier transactions."
            )
        if horizon_days > T:
            limitations.insert(
                0,
                f"Data limitation: Requested horizon ({horizon_days} days) exceeds historical observations ({T} days). "
                f"Long-term uncertainty increases noticeably over time."
            )

        return {
            "dataset_id": dataset_id,
            "file_name": dataset.file_name,
            "currency": currency,
            "horizon_days": horizon_days,
            "historical_data": historical_points,
            "forecast_data": forecast_points,
            "summary": {
                "total_historical_revenue": total_hist_rev,
                "average_daily_historical_revenue": avg_hist_rev,
                "total_projected_revenue": total_fc_rev,
                "average_daily_projected_revenue": avg_fc_rev,
                "projected_change_percent": change_pct,
                "historical_days_count": T,
                "forecast_days_count": horizon_days,
                "historical_start_date": start_date.strftime("%Y-%m-%d"),
                "historical_end_date": end_date.strftime("%Y-%m-%d"),
                "forecast_start_date": (end_date + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
                "forecast_end_date": (end_date + pd.Timedelta(days=horizon_days)).strftime("%Y-%m-%d"),
            },
            "model_metadata": {
                "method": "Holt Damped Linear Trend Exponential Smoothing",
                "smoothing_level_alpha": alpha,
                "smoothing_trend_beta": beta,
                "damping_phi": phi,
                "confidence_interval_level": interval_label,
                "interval_uncertainty_note": uncertainty_note,
                "held_out_evaluation": evaluation_meta,
                "assumptions": assumptions,
                "limitations": limitations
            }
        }

    finally:
        db.close()
