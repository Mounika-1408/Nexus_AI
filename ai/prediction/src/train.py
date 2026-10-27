import os
import sys
import json
import joblib
import sklearn
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

# Add current directory to path if necessary
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import load_sales_data, inspect_dataset
from src.preprocessing import preprocess_data
from src.evaluate import evaluate_predictions

MODELS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "models"
)


def train_and_evaluate():
    """
    Main training pipeline for the Sales Prediction module.
    Performs 5-fold CV model selection, held-out test evaluation, computes feature
    ranges for extrapolation detection, and saves model, preprocessor, and metrics.json.
    """
    print("=" * 60)
    print("      NEXUS_AI SALES PREDICTION - ML TRAINING PIPELINE      ")
    print("=" * 60)

    # 1. Dataset Inspection & Loading
    df = load_sales_data()
    eda_info = inspect_dataset(df)

    print("\n1. DATASET INSPECTION")
    print(f"   Shape            : {eda_info['shape']} ({eda_info['rows']} rows, {eda_info['columns_count']} columns)")
    print(f"   Columns          : {eda_info['column_names']}")

    # 2. Data Preprocessing & Feature/Target separation
    target_col = "Sales"
    X, y, preprocessor = preprocess_data(df, target_column=target_col)
    
    # Feature ranges for extrapolation checking (A4 fix)
    feature_ranges = {}
    for col in preprocessor.feature_names:
        feature_ranges[col] = {
            "min": round(float(df[col].min()), 2),
            "max": round(float(df[col].max()), 2),
            "mean": round(float(df[col].mean()), 2),
            "std": round(float(df[col].std()), 2)
        }

    # 3. Train-Test Split (80% Train, 20% Test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )

    # Fit preprocessor on training features to prevent data leakage
    X_train_scaled = preprocessor.fit_transform(X_train)
    X_test_scaled = preprocessor.transform(X_test)

    # 4. Model Training, 5-Fold Cross Validation, and Test Evaluation (A3 fix)
    candidate_models = {
        "Linear Regression": LinearRegression(),
        "Ridge Regression": Ridge(alpha=1.0, random_state=42),
        "Random Forest Regressor": RandomForestRegressor(n_estimators=100, random_state=42),
        "Gradient Boosting Regressor": GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, random_state=42),
    }

    results = {}
    cv_results = {}
    best_model_name = None
    best_r2 = -float("inf")
    best_model_obj = None

    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    print("\n3. MODEL EVALUATION & COMPARISON")
    print("-" * 75)
    print(f"{'Model':<30} | {'CV R² (mean±std)':<18} | {'Test R²':<8} | {'Test MAE':<8}")
    print("-" * 75)

    for name, model in candidate_models.items():
        # 5-Fold Cross Validation on Train Split
        cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=kf, scoring="r2")
        cv_mean = float(np.mean(cv_scores))
        cv_std = float(np.std(cv_scores))
        cv_results[name] = {"cv_mean_r2": round(cv_mean, 4), "cv_std_r2": round(cv_std, 4)}

        # Fit model on full training split
        model.fit(X_train_scaled, y_train)
        
        # Predict on held-out test split
        y_pred = model.predict(X_test_scaled)
        metrics = evaluate_predictions(y_test, y_pred)
        results[name] = metrics

        print(f"{name:<30} | {cv_mean:.4f} ± {cv_std:.4f}    | {metrics['R2']:<8.4f} | {metrics['MAE']:<8.4f}")

        if metrics["R2"] > best_r2:
            best_r2 = metrics["R2"]
            best_model_name = name
            best_model_obj = model

    print("-" * 75)
    print(f"\n4. BEST MODEL SELECTION: {best_model_name} (Test R² = {best_r2:.4f})")

    # 5. Save Artifacts & metrics.json (A2 fix)
    os.makedirs(MODELS_DIR, exist_ok=True)
    model_path = os.path.join(MODELS_DIR, "best_model.joblib")
    preprocessor_path = os.path.join(MODELS_DIR, "preprocessor.joblib")
    metrics_path = os.path.join(MODELS_DIR, "metrics.json")

    joblib.dump(best_model_obj, model_path)
    joblib.dump(preprocessor, preprocessor_path)

    metrics_payload = {
        "model_name": best_model_name,
        "test_metrics": {
            "r2": round(results[best_model_name]["R2"], 4),
            "mae": round(results[best_model_name]["MAE"], 4),
            "rmse": round(results[best_model_name]["RMSE"], 4),
            "mape": round(results[best_model_name]["MAPE"], 2)
        },
        "cv_metrics": cv_results[best_model_name],
        "feature_ranges": feature_ranges,
        "candidate_models": {
            k: {
                "test_r2": round(results[k]["R2"], 4),
                "test_mae": round(results[k]["MAE"], 4),
                "test_rmse": round(results[k]["RMSE"], 4),
                "cv_r2": cv_results[k]["cv_mean_r2"]
            }
            for k in results
        },
        "dataset_info": {
            "total_samples": eda_info["rows"],
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "features": preprocessor.feature_names,
            "target": target_col,
            "units": "Expenditure: thousands of USD ($k), Sales: thousands of units"
        },
        "sklearn_version": sklearn.__version__,
        "random_state": 42
    }

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2)

    print(f"   Model Saved To        : {model_path}")
    print(f"   Preprocessor Saved To : {preprocessor_path}")
    print(f"   Metrics Saved To      : {metrics_path}")

    return metrics_payload


if __name__ == "__main__":
    train_and_evaluate()
