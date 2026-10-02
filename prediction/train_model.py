from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

from preprocessing import DataPreprocessor
from utils import save_model, evaluate_model


# ============================================================
# Project paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DATA_PATH = (
    BASE_DIR
    / "datasets"
    / "raw"
    / "sales_data_file.csv"
)

PROCESSED_DATA_PATH = (
    BASE_DIR
    / "datasets"
    / "processed"
    / "sales_clean.csv"
)

MODEL_PATH = (
    BASE_DIR
    / "models"
    / "sales_linear_regression.pkl"
)


# ============================================================
# Train Model
# ============================================================

def train_model():

    print("\n========== NexusAI Sales Prediction ==========\n")

    # --------------------------------------------------------
    # Step 1: Preprocess dataset
    # --------------------------------------------------------

    processor = DataPreprocessor(
        RAW_DATA_PATH,
        PROCESSED_DATA_PATH
    )

    df = processor.preprocess()

    # --------------------------------------------------------
    # Step 2: Define input features and target
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Step 3: Split dataset
    # --------------------------------------------------------

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )

    print("\n========== Dataset Split ==========")
    print(f"Training samples: {len(X_train)}")
    print(f"Testing samples : {len(X_test)}")

    # --------------------------------------------------------
    # Step 4: Create model
    # --------------------------------------------------------

    model = LinearRegression()

    # --------------------------------------------------------
    # Step 5: Train model
    # --------------------------------------------------------

    print("\nTraining Linear Regression model...")

    model.fit(
        X_train,
        y_train
    )

    print("Model training completed.")

    # --------------------------------------------------------
    # Step 6: Make predictions
    # --------------------------------------------------------

    predictions = model.predict(X_test)

    # --------------------------------------------------------
    # Step 7: Evaluate model
    # --------------------------------------------------------

    metrics = evaluate_model(
        y_test,
        predictions
    )

    # --------------------------------------------------------
    # Step 8: Display model coefficients
    # --------------------------------------------------------

    print("\n========== Model Coefficients ==========")

    print(f"TV coefficient        : {model.coef_[0]:.4f}")
    print(f"Radio coefficient     : {model.coef_[1]:.4f}")
    print(f"Newspaper coefficient : {model.coef_[2]:.4f}")
    print(f"Intercept              : {model.intercept_:.4f}")

    # --------------------------------------------------------
    # Step 9: Save trained model
    # --------------------------------------------------------

    save_model(
        model,
        MODEL_PATH
    )

    print("\n========== Training Complete ==========")
    print(f"Model saved at:\n{MODEL_PATH}")

    return model, metrics


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    train_model()