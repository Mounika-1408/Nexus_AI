import pickle
from pathlib import Path

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)


def save_model(model, model_path):
    """
    Save a trained machine learning model.
    """

    model_path = Path(model_path)

    model_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(model_path, "wb") as file:
        pickle.dump(model, file)

    print(f"Model saved successfully:")
    print(model_path)


def load_model(model_path):
    """
    Load a previously trained machine learning model.
    """

    model_path = Path(model_path)

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model not found: {model_path}"
        )

    with open(model_path, "rb") as file:
        model = pickle.load(file)

    return model


def evaluate_model(y_true, y_pred):
    """
    Evaluate the prediction model.
    """

    mae = mean_absolute_error(
        y_true,
        y_pred
    )

    mse = mean_squared_error(
        y_true,
        y_pred
    )

    rmse = mse ** 0.5

    r2 = r2_score(
        y_true,
        y_pred
    )

    metrics = {
        "MAE": mae,
        "MSE": mse,
        "RMSE": rmse,
        "R2": r2
    }

    print("\n========== Model Evaluation ==========")
    print(f"MAE      : {mae:.2f}")
    print(f"MSE      : {mse:.2f}")
    print(f"RMSE     : {rmse:.2f}")
    print(f"R2 Score : {r2:.4f}")

    return metrics