from pathlib import Path

import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor

from xgboost import XGBRegressor

from utils import evaluate_model


# ============================================================
# Project Paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = (
    BASE_DIR
    / "datasets"
    / "processed"
    / "sales_clean.csv"
)


# ============================================================
# Load Dataset
# ============================================================

def load_dataset():

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Processed dataset not found: {DATA_PATH}"
        )

    df = pd.read_csv(DATA_PATH)

    print("\nDataset loaded successfully.")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    return df


# ============================================================
# Main Model Comparison
# ============================================================

def compare_models():

    print("\n========== NexusAI Model Comparison ==========\n")

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    df = load_dataset()

    # --------------------------------------------------------
    # Features and target
    # --------------------------------------------------------

    X = df[
        [
            "tv",
            "radio",
            "newspaper"
        ]
    ]

    y = df["sales"]

    # --------------------------------------------------------
    # Same train/test split for every model
    # --------------------------------------------------------

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )

    print("\nTraining samples:", len(X_train))
    print("Testing samples :", len(X_test))

    # --------------------------------------------------------
    # Define models
    # --------------------------------------------------------

    models = {

        "Linear Regression": LinearRegression(),

        "Random Forest": RandomForestRegressor(
            n_estimators=200,
            random_state=42
        ),

        "XGBoost": XGBRegressor(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=3,
            random_state=42,
            objective="reg:squarederror"
        )
    }

    results = {}

    # --------------------------------------------------------
    # Train and evaluate each model
    # --------------------------------------------------------

    for model_name, model in models.items():

        print("\n" + "=" * 50)
        print(f"Training {model_name}")
        print("=" * 50)

        model.fit(
            X_train,
            y_train
        )

        predictions = model.predict(X_test)

        metrics = evaluate_model(
            y_test,
            predictions
        )

        results[model_name] = metrics

    # --------------------------------------------------------
    # Display comparison
    # --------------------------------------------------------

    print("\n\n========== MODEL COMPARISON ==========\n")

    print(
        f"{'Model':<20}"
        f"{'MAE':>12}"
        f"{'RMSE':>12}"
        f"{'R²':>12}"
    )

    print("-" * 56)

    for model_name, metrics in results.items():

        print(
            f"{model_name:<20}"
            f"{metrics['MAE']:>12.4f}"
            f"{metrics['RMSE']:>12.4f}"
            f"{metrics['R2']:>12.4f}"
        )

    return results


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    compare_models()