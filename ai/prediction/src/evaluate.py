import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from typing import Dict

def evaluate_predictions(y_true, y_pred) -> Dict[str, float]:
    """
    Calculate regression evaluation metrics: MAE, RMSE, MSE, R², and MAPE.
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    mae = float(mean_absolute_error(y_true, y_pred))
    mse = float(mean_squared_error(y_true, y_pred))
    rmse = float(np.sqrt(mse))
    r2 = float(r2_score(y_true, y_pred))
    
    # Safe MAPE calculation
    non_zero_mask = y_true != 0
    if np.any(non_zero_mask):
        mape = float(np.mean(np.abs((y_true[non_zero_mask] - y_pred[non_zero_mask]) / y_true[non_zero_mask])) * 100)
    else:
        mape = 0.0

    return {
        "MAE": round(mae, 4),
        "MSE": round(mse, 4),
        "RMSE": round(rmse, 4),
        "R2": round(r2, 4),
        "MAPE": round(mape, 4),
    }

def print_metrics(model_name: str, metrics: Dict[str, float]):
    """
    Print model evaluation metrics in a readable tabular format.
    """
    print(f"\n--- {model_name} Evaluation ---")
    for metric_name, val in metrics.items():
        print(f"  {metric_name:6s}: {val:.4f}")
