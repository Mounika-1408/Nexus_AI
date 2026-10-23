"""
NexusAI Central Currency Normalization Service
Establishes USD as the primary base currency for financial aggregation.
Reference Exchange Rates: Benchmark rates as of Q1 2026 (matching sample dataset period).
"""

from typing import Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

# System-wide Base Currency for all normalized financial aggregation
BASE_CURRENCY = "USD"

# Explicit Reference Exchange Rates (nominal units of currency per 1.0 USD)
# Documented source: European Central Bank & IMF benchmark reference rates (Q1 2026)
FX_RATES_TO_BASE: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "INR": 83.50,
    "JPY": 155.0,
    "CAD": 1.36,
    "AUD": 1.52,
}

SUPPORTED_CURRENCIES = set(FX_RATES_TO_BASE.keys())


def normalize_currency_code(currency: Any) -> Optional[str]:
    """
    Sanitize and validate currency string.
    Returns uppercase 3-letter code or None if missing/invalid.
    """
    if currency is None or pd.isna(currency):
        return None
    curr_str = str(currency).strip().upper()
    if not curr_str or curr_str in ["NAN", "NONE", "NULL", ""]:
        return None
    return curr_str


def is_supported_currency(currency: Any) -> bool:
    """
    Check if currency is recognized and has a valid conversion rate to BASE_CURRENCY.
    """
    code = normalize_currency_code(currency)
    return code is not None and code in SUPPORTED_CURRENCIES


def get_exchange_rate_to_base(currency: Any) -> float:
    """
    Get units of foreign currency per 1.0 USD base currency.
    Raises ValueError if currency is missing or unsupported.
    """
    code = normalize_currency_code(currency)
    if not code:
        raise ValueError("Currency code is missing or empty.")
    if code not in FX_RATES_TO_BASE:
        raise ValueError(
            f"Unsupported currency code '{code}'. Supported currencies are: "
            f"{', '.join(sorted(SUPPORTED_CURRENCIES))}."
        )
    return FX_RATES_TO_BASE[code]


def convert_to_base_currency(amount: Optional[float], currency: Any) -> Tuple[Optional[float], float]:
    """
    Convert an amount in foreign currency to BASE_CURRENCY (USD).
    Returns (normalized_amount_rounded_2_decimals, exchange_rate).
    """
    if amount is None or pd.isna(amount):
        return None, 1.0

    rate = get_exchange_rate_to_base(currency)
    normalized = round(float(amount) / rate, 2)
    return normalized, rate
