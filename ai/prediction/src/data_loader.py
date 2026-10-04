import os
import pandas as pd
from typing import Tuple, Dict, Any

DEFAULT_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "sales data file.csv"
)

def load_sales_data(filepath: str = DEFAULT_DATA_PATH) -> pd.DataFrame:
    """
    Load the Kaggle Sales Prediction dataset from CSV file.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset file not found at path: {filepath}")
    
    df = pd.read_csv(filepath)
    return df

def inspect_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform exploratory data analysis (EDA) and return key dataset statistics.
    """
    info = {
        "shape": df.shape,
        "rows": df.shape[0],
        "columns_count": df.shape[1],
        "column_names": df.columns.tolist(),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "missing_values": df.isnull().sum().to_dict(),
        "total_missing": int(df.isnull().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "summary_statistics": df.describe().to_dict(),
    }
    return info

if __name__ == "__main__":
    df = load_sales_data()
    info = inspect_dataset(df)
    print("=== DATASET INSPECTION ===")
    print(f"Shape: {info['shape']} (Rows: {info['rows']}, Columns: {info['columns_count']})")
    print(f"Columns: {info['column_names']}")
    print(f"Data Types: {info['dtypes']}")
    print(f"Missing Values: {info['missing_values']}")
    print(f"Duplicate Rows: {info['duplicate_rows']}")
    print("\nDescriptive Statistics:")
    print(df.describe())
