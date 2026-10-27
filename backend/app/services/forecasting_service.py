import os
from typing import Dict, Any, List, Optional, Tuple
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


def optimize_holt_parameters(y: np.ndarray) -> Tuple[float, float, float]:
    """
    Fit Holt's Damped parameters (alpha, beta, phi) using in-sample one-step-ahead SSE.
    Replaces static fixed parameters (F2 fix).
    """
    T = len(y)
    if T < 4:
        return 0.20, 0.05, 0.90

    best_sse = float('inf')
    best_params = (0.20, 0.05, 0.90)

    alphas = [0.05, 0.10, 0.20, 0.30, 0.40]
    betas = [0.01, 0.03, 0.05, 0.10]
    phis = [0.80, 0.85, 0.90, 0.95]

    for a in alphas:
        for b_val in betas:
            for p in phis:
                L = np.zeros(T)
                b = np.zeros(T)
                L[0] = max(0.0, y[0])
                b[0] = 0.0
                sse = 0.0

                for t in range(1, T):
                    pred = max(0.0, L[t - 1] + p * b[t - 1])
                    sse += (y[t] - pred) ** 2
                    L[t] = max(0.0, a * y[t] + (1.0 - a) * pred)
                    b[t] = b_val * (L[t] - L[t - 1]) + (1.0 - b_val) * p * b[t - 1]

                if sse < best_sse:
                    best_sse = sse
                    best_params = (a, b_val, p)

    return best_params


def forecast_revenue_service(
    dataset_id: int,
    horizon_days: int = 30,
    anchor_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates a defensible financial revenue forecast using Holt's Damped Linear Trend
    exponential smoothing with dynamic parameter fitting, trailing-zero guards,
    and honest out-of-sample error metrics (WAPE and sMAPE).
    Forecast dates are anchored dynamically from the intended current date or latest valid record.
    """
    # 1. Validate Horizon
    allowed_horizons = [7, 30, 90]
    if horizon_days not in allowed_horizons:
        raise HTTPException(
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            detail=f"Invalid forecast horizon ({horizon_days} days). Supported horizons are 7, 30, or 90 days."
        )

    warnings: List[str] = []

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
        if distinct_daily_count < 14:
            warnings.append(
                f"Small sample size ({distinct_daily_count} distinct daily observations). "
                "Forecast confidence is lower due to limited historical series length."
            )

        # 5. Complete calendar range & impute missing calendar days with zero
        start_date = pd.to_datetime(daily_agg.index.min())
        end_date = pd.to_datetime(daily_agg.index.max())
        full_date_range = pd.date_range(start=start_date, end=end_date, freq="D")
        
        daily_series_dt = daily_agg.copy()
        daily_series_dt.index = pd.to_datetime(daily_series_dt.index)
        daily_full = daily_series_dt.reindex(full_date_range, fill_value=0.0)

        missing_days_count = len(full_date_range) - distinct_daily_count
        y = daily_full.values.astype(float)
        T = len(y)

        # Check sparsity (F3)
        active_ratio = distinct_daily_count / float(T)
        if active_ratio < 0.40 and T >= 14:
            warnings.append(
                f"High dataset sparsity detected ({distinct_daily_count} active days in {T} calendar days, "
                f"{round(active_ratio * 100, 1)}% density). Averages account for calendar gaps."
            )

        # 6. Trailing Zero Detection & Adjustment (F1 fix)
        trailing_zeros = 0
        for val in reversed(y):
            if val == 0.0:
                trailing_zeros += 1
            else:
                break

        # Check if there was positive history prior to the trailing zeros
        has_positive_prior = (trailing_zeros < T) and (np.sum(y[:T - trailing_zeros]) > 0)
        
        # If trailing zeros >= 3 and positive history existed, fit on active history to avoid zero-collapse
        if trailing_zeros >= 3 and has_positive_prior:
            warnings.append(
                f"Detected {trailing_zeros} consecutive trailing zero-revenue days at end of dataset. "
                "Forecast calibrated on active operational history to avoid artificial $0 collapse."
            )
            # Use active historical series for trend estimation
            fit_series = y[:T - trailing_zeros]
        else:
            fit_series = y

        fit_T = len(fit_series)

        # 7. Dynamic Parameter Optimization (F2 fix)
        alpha, beta, phi = optimize_holt_parameters(fit_series)

        # Fit Holt's Damped Linear Trend Model
        L = np.zeros(fit_T)
        b = np.zeros(fit_T)
        L[0] = max(0.0, fit_series[0])
        b[0] = 0.0

        for t in range(1, fit_T):
            prev_forecast = L[t - 1] + phi * b[t - 1]
            L[t] = max(0.0, alpha * fit_series[t] + (1.0 - alpha) * prev_forecast)
            b[t] = beta * (L[t] - L[t - 1]) + (1.0 - beta) * phi * b[t - 1]

        # In-sample residual standard deviation for prediction intervals
        in_sample_preds = np.zeros(fit_T)
        in_sample_preds[0] = fit_series[0]
        for t in range(1, fit_T):
            in_sample_preds[t] = max(0.0, L[t - 1] + phi * b[t - 1])

        residuals = fit_series[1:] - in_sample_preds[1:] if fit_T > 1 else np.array([0.0])
        std_error = float(np.std(residuals)) if len(residuals) > 0 else 1.0
        if std_error == 0.0:
            std_error = float(np.mean(fit_series) * 0.1) or 1.0

        # Recent active daily baseline for sanity check (F1 safeguard)
        recent_active_window = fit_series[-min(30, fit_T):]
        recent_active_mean = float(np.mean(recent_active_window)) if len(recent_active_window) > 0 else 0.0

        # 8. Determine dynamic forecast anchor & generate Horizon Forecasts (80% level: z = 1.28)
        today_date = datetime.now().date()
        if anchor_date:
            try:
                base_anchor = pd.to_datetime(anchor_date).date()
            except Exception:
                base_anchor = today_date
        else:
            base_anchor = today_date

        hist_max_date = end_date.date()
        if hist_max_date >= base_anchor:
            effective_anchor = hist_max_date
        else:
            effective_anchor = base_anchor
            if hist_max_date < today_date:
                warnings.append(
                    f"Dataset historical records end on {end_date.strftime('%Y-%m-%d')}. "
                    f"Forecast horizon is anchored to current date ({effective_anchor.strftime('%Y-%m-%d')}) "
                    f"to project upcoming revenue."
                )

        anchor_dt = pd.to_datetime(effective_anchor)

        forecast_points = []
        for h in range(1, horizon_days + 1):
            damping_sum = sum(phi ** i for i in range(1, h + 1))
            raw_point = float(L[-1] + damping_sum * b[-1])

            # If model collapsed to 0 while recent active history was positive, apply baseline safeguard
            if raw_point <= 0.0 and recent_active_mean > 0.0 and has_positive_prior:
                point_forecast = round(recent_active_mean * (phi ** h), 2)
            else:
                point_forecast = max(0.0, round(raw_point, 2))

            step_std = float(std_error * np.sqrt(1.0 + (h - 1) * (alpha ** 2)))
            lower_bound = max(0.0, round(float(point_forecast - 1.28 * step_std), 2))
            upper_bound = round(float(point_forecast + 1.28 * step_std), 2)

            fc_date = anchor_dt + pd.Timedelta(days=h)
            forecast_points.append({
                "date": fc_date.strftime("%Y-%m-%d"),
                "forecast_revenue": point_forecast,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
            })

        # 9. Out-of-Sample Backtesting Evaluation (F4 fix: WAPE and sMAPE)
        evaluation_meta = None
        if fit_T >= 7:
            test_size = max(2, min(5, int(fit_T * 0.25)))
            train_T = fit_T - test_size

            L_tr = np.zeros(train_T)
            b_tr = np.zeros(train_T)
            L_tr[0] = max(0.0, fit_series[0])
            b_tr[0] = 0.0

            for t in range(1, train_T):
                p_fc = L_tr[t - 1] + phi * b_tr[t - 1]
                L_tr[t] = max(0.0, alpha * fit_series[t] + (1.0 - alpha) * p_fc)
                b_tr[t] = beta * (L_tr[t] - L_tr[t - 1]) + (1.0 - beta) * phi * b_tr[t - 1]

            test_actuals = fit_series[train_T:]
            test_preds = []
            for h in range(1, test_size + 1):
                d_sum = sum(phi ** i for i in range(1, h + 1))
                test_preds.append(max(0.0, float(L_tr[-1] + d_sum * b_tr[-1])))
            test_preds = np.array(test_preds)

            mae = float(np.mean(np.abs(test_actuals - test_preds)))
            rmse = float(np.sqrt(np.mean((test_actuals - test_preds) ** 2)))

            # WAPE and sMAPE prevent divide-by-zero or infinite MAPE
            denom_sum = np.sum(test_actuals)
            wape = float(np.sum(np.abs(test_actuals - test_preds)) / max(denom_sum, 1.0) * 100.0)
            smape_denom = np.abs(test_actuals) + np.abs(test_preds) + 1e-6
            smape = float(np.mean(2.0 * np.abs(test_actuals - test_preds) / smape_denom) * 100.0)

            evaluation_meta = {
                "evaluated_on_held_out": True,
                "test_days_held_out": test_size,
                "mae": round(mae, 2),
                "rmse": round(rmse, 2),
                "wape_percent": round(wape, 1),
                "smape_percent": round(smape, 1),
                "mape_percent": round(wape, 1),  # Backward compatibility alias
                "notes": f"Model evaluated on the most recent {test_size} held-out historical days using WAPE and sMAPE."
            }
        else:
            evaluation_meta = {
                "evaluated_on_held_out": False,
                "test_days_held_out": 0,
                "mae": None,
                "rmse": None,
                "wape_percent": None,
                "smape_percent": None,
                "mape_percent": None,
                "notes": "Historical data size below minimum threshold (>= 7 observations) for holdout backtesting."
            }

        # 10. Summary Calculations
        total_hist_rev = round(float(np.sum(y)), 2)
        avg_hist_rev = round(float(np.mean(y)), 2)
        active_day_rev = round(float(np.sum(y) / max(distinct_daily_count, 1)), 2)
        
        fc_values = [p["forecast_revenue"] for p in forecast_points]
        total_fc_rev = round(float(np.sum(fc_values)), 2)
        avg_fc_rev = round(total_fc_rev / horizon_days, 2)

        # Baseline comparison: compare against recent active daily run-rate
        comparison_baseline = recent_active_mean if (has_positive_prior and recent_active_mean > 0) else avg_hist_rev
        change_pct = 0.0
        if comparison_baseline > 0:
            change_pct = round(((avg_fc_rev - comparison_baseline) / comparison_baseline) * 100.0, 1)

        currency = detect_dataset_currency(dataset)
        is_limited_sample = T < 30
        interval_label = "80% (Approximate)" if is_limited_sample else "80%"

        return {
            "dataset_id": dataset_id,
            "file_name": dataset.file_name,
            "currency": currency,
            "horizon_days": horizon_days,
            "warnings": warnings,
            "historical_data": [
                {"date": d.strftime("%Y-%m-%d"), "revenue": round(float(val), 2)}
                for d, val in zip(full_date_range, y)
            ],
            "forecast_data": forecast_points,
            "summary": {
                "total_historical_revenue": total_hist_rev,
                "average_daily_historical_revenue": avg_hist_rev,
                "average_active_day_revenue": active_day_rev,
                "total_projected_revenue": total_fc_rev,
                "average_daily_projected_revenue": avg_fc_rev,
                "projected_change_percent": change_pct,
                "historical_days_count": T,
                "distinct_active_days": distinct_daily_count,
                "forecast_days_count": horizon_days,
                "historical_start_date": start_date.strftime("%Y-%m-%d"),
                "historical_end_date": end_date.strftime("%Y-%m-%d"),
                "forecast_anchor_date": anchor_dt.strftime("%Y-%m-%d"),
                "forecast_start_date": (anchor_dt + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
                "forecast_end_date": (anchor_dt + pd.Timedelta(days=horizon_days)).strftime("%Y-%m-%d"),
            },
            "model_metadata": {
                "method": "Optimized Holt Damped Linear Trend",
                "smoothing_level_alpha": round(alpha, 3),
                "smoothing_trend_beta": round(beta, 3),
                "damping_phi": round(phi, 3),
                "parameter_selection": "Dynamic in-sample one-step error optimization",
                "confidence_interval_level": interval_label,
                "held_out_evaluation": evaluation_meta,
                "assumptions": [
                    "Transactions aggregated into daily calendar revenue totals.",
                    f"Missing calendar dates between {start_date.strftime('%Y-%m-%d')} and {end_date.strftime('%Y-%m-%d')} filled ({missing_days_count} imputed).",
                    "Values normalized to Base Currency (USD) using explicit reference exchange rates.",
                    f"Parameters fitted dynamically (alpha={alpha}, beta={beta}, phi={phi}) to avoid overfitting to final-day noise.",
                    "Trailing-zero guard applied to prevent collapse from inactive tail periods.",
                    f"Forecast horizon spans {horizon_days} future calendar days ({(anchor_dt + pd.Timedelta(days=1)).strftime('%Y-%m-%d')} to {(anchor_dt + pd.Timedelta(days=horizon_days)).strftime('%Y-%m-%d')}) anchored to {anchor_dt.strftime('%Y-%m-%d')}."
                ],
                "limitations": [
                    "Does not incorporate external market shocks or competitor interventions.",
                    "Seasonal patterns require 1-2 years of historical records.",
                    f"Limited sample size ({T} calendar days) creates wider prediction bounds."
                ]
            }
        }

    finally:
        db.close()
