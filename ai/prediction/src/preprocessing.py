import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from typing import Tuple, List, Optional

class DataPreprocessor:
    """
    Preprocessor class to handle feature scaling, missing values, and data preparation.
    """
    def __init__(self, feature_names: Optional[List[str]] = None):
        self.feature_names = feature_names or ["TV", "Radio", "Newspaper"]
        self.scaler = StandardScaler()
        self.is_fitted = False

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean missing values and duplicate rows from dataframe.
        """
        df_clean = df.copy()
        # Remove duplicate records if any exist
        df_clean = df_clean.drop_duplicates()
        # Fill missing numeric values with column median if any exist
        num_cols = df_clean.select_dtypes(include=[np.number]).columns
        for col in num_cols:
            if df_clean[col].isnull().sum() > 0:
                df_clean[col] = df_clean[col].fillna(df_clean[col].median())
        return df_clean

    def fit_transform(self, X: pd.DataFrame) -> np.ndarray:
        """
        Fit the scaler on features X and transform them.
        """
        X_feats = X[self.feature_names]
        X_scaled = self.scaler.fit_transform(X_feats)
        self.is_fitted = True
        return X_scaled

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """
        Transform features X using the fitted scaler.
        """
        if not self.is_fitted:
            raise ValueError("DataPreprocessor has not been fitted yet. Call fit_transform first.")
        X_feats = X[self.feature_names]
        return self.scaler.transform(X_feats)

def preprocess_data(df: pd.DataFrame, target_column: str = "Sales") -> Tuple[pd.DataFrame, pd.Series, DataPreprocessor]:
    """
    Clean dataset, separate features (X) and target (y), and fit preprocessor scaler.
    """
    preprocessor = DataPreprocessor()
    df_clean = preprocessor.clean_data(df)
    
    if target_column not in df_clean.columns:
        raise ValueError(f"Target column '{target_column}' not found in dataframe. Available columns: {df_clean.columns.tolist()}")
    
    feature_cols = [col for col in df_clean.columns if col != target_column]
    preprocessor.feature_names = feature_cols
    
    X = df_clean[feature_cols]
    y = df_clean[target_column]
    
    return X, y, preprocessor

def prepare_features(input_dict: dict, feature_names: List[str] = ["TV", "Radio", "Newspaper"]) -> pd.DataFrame:
    """
    Convert single prediction dictionary or list of dicts to pandas DataFrame with proper feature ordering.
    """
    if isinstance(input_dict, dict):
        df_input = pd.DataFrame([input_dict])
    else:
        df_input = pd.DataFrame(input_dict)
    
    for col in feature_names:
        if col not in df_input.columns:
            raise ValueError(f"Missing required feature column '{col}' in input.")
            
    return df_input[feature_names]
