from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor

from utils import save_model, evaluate_model


# ============================================================
# Paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = (
    BASE_DIR
    / "datasets"
    / "processed"
    / "sales_clean.csv"
)

MODEL_PATH = (
    BASE_DIR
    / "models"
    / "sales_random_forest.pkl"
)


# ============================================================
# Train Random Forest
# ============================================================

def train_random_forest():

    print("\n========== NexusAI Random Forest Training ==========\n")

    # Load processed dataset
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Processed dataset not found: {DATA_PATH}"
        )

    df = pd.read_csv(DATA_PATH)

    print("Dataset loaded successfully.")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    # Features and target
    X = df[
        [
            "tv",
            "radio",
            "newspaper"
        ]
    ]

    y = df["sales"]

    print("\n========== Features and Target ==========")

    print("Features:")
    print(" - TV")
    print(" - Radio")
    print(" - Newspaper")

    print("\nTarget:")
    print(" - Sales")

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )

    print("\n========== Dataset Split ==========")
    print(f"Training samples: {len(X_train)}")
    print(f"Testing samples : {len(X_test)}")

    # Create Random Forest model
    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42
    )

    print("\nTraining Random Forest model...")

    # Train
    model.fit(X_train, y_train)

    print("Model training completed.")

    # Predictions
    predictions = model.predict(X_test)

    # Evaluation
    metrics = evaluate_model(
        y_test,
        predictions
    )

    # Feature importance
    print("\n========== Feature Importance ==========")

    for feature, importance in zip(
        X.columns,
        model.feature_importances_
    ):
        print(
            f"{feature:<12}: {importance:.4f}"
        )

    # Save model
    save_model(
        model,
        MODEL_PATH
    )

    print("\n========== Training Complete ==========")
    print(f"Model saved at:")
    print(MODEL_PATH)

    return model, metrics


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    train_random_forest()