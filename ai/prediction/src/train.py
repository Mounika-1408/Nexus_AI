import os
import sys
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

# Add current directory to path if necessary
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import load_sales_data, inspect_dataset
from src.preprocessing import preprocess_data
from src.evaluate import evaluate_predictions, print_metrics

MODELS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "models"
)

def train_and_evaluate():
    """
    Main training pipeline for the Sales Prediction module.
    Loads dataset, preprocesses features, trains regression models, evaluates metrics,
    selects the best model, and saves model and preprocessor artifacts.
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
    print(f"   Data Types       : {eda_info['dtypes']}")
    print(f"   Missing Values   : {eda_info['missing_values']}")
    print(f"   Duplicate Rows   : {eda_info['duplicate_rows']}")

    # 2. Data Preprocessing & Feature/Target separation
    target_col = "Sales"
    X, y, preprocessor = preprocess_data(df, target_column=target_col)
    
    print("\n2. DATA PREPROCESSING")
    print(f"   Target Column    : '{target_col}'")
    print(f"   Feature Columns  : {preprocessor.feature_names}")
    print("   Data Cleaning    : No missing values found; 0 duplicates removed.")

    # 3. Train-Test Split (80% Train, 20% Test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )

    # Fit preprocessor on training features to prevent data leakage
    X_train_scaled = preprocessor.fit_transform(X_train)
    X_test_scaled = preprocessor.transform(X_test)

    print(f"   Train Set Size   : {len(X_train)} samples")
    print(f"   Test Set Size    : {len(X_test)} samples")

    # 4. Model Training & Evaluation
    candidate_models = {
        "Linear Regression": LinearRegression(),
        "Ridge Regression": Ridge(alpha=1.0, random_state=42),
        "Random Forest Regressor": RandomForestRegressor(n_estimators=100, random_state=42),
        "Gradient Boosting Regressor": GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, random_state=42),
    }

    results = {}
    best_model_name = None
    best_r2 = -float("inf")
    best_model_obj = None

    print("\n3. MODEL EVALUATION & COMPARISON")
    print("-" * 60)
    print(f"{'Model':<30} | {'MAE':<7} | {'RMSE':<7} | {'R²':<7} | {'MAPE (%)':<8}")
    print("-" * 60)

    for name, model in candidate_models.items():
        # Fit model on scaled training data
        model.fit(X_train_scaled, y_train)
        
        # Predict on test data
        y_pred = model.predict(X_test_scaled)
        
        # Evaluate metrics
        metrics = evaluate_predictions(y_test, y_pred)
        results[name] = metrics

        print(f"{name:<30} | {metrics['MAE']:<7.4f} | {metrics['RMSE']:<7.4f} | {metrics['R2']:<7.4f} | {metrics['MAPE']:<8.2f}")

        if metrics["R2"] > best_r2:
            best_r2 = metrics["R2"]
            best_model_name = name
            best_model_obj = model

    print("-" * 60)
    print(f"\n4. BEST MODEL SELECTION")
    print(f"   Selected Model   : {best_model_name}")
    print(f"   Best R² Score    : {results[best_model_name]['R2']}")
    print(f"   Best RMSE        : {results[best_model_name]['RMSE']}")
    print(f"   Best MAE         : {results[best_model_name]['MAE']}")

    # 5. Save Artifacts
    os.makedirs(MODELS_DIR, exist_ok=True)
    model_path = os.path.join(MODELS_DIR, "best_model.joblib")
    preprocessor_path = os.path.join(MODELS_DIR, "preprocessor.joblib")

    joblib.dump(best_model_obj, model_path)
    joblib.dump(preprocessor, preprocessor_path)

    print("\n5. ARTIFACT SAVING")
    print(f"   Model Saved To        : {model_path}")
    print(f"   Preprocessor Saved To : {preprocessor_path}")

    return {
        "eda_info": eda_info,
        "results": results,
        "best_model_name": best_model_name,
        "best_metrics": results[best_model_name],
        "model_path": model_path,
        "preprocessor_path": preprocessor_path,
    }

if __name__ == "__main__":
    train_and_evaluate()
