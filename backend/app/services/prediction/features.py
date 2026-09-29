"""
Feature engineering for prediction models.

Builds features from stored metrics: lag values, rolling stats, growth rates.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from app.core.logging import get_logger

logger = get_logger(__name__)


def build_features(
    dates: List[date],
    values: List[float],
    lag_days: List[int] = None,
    rolling_windows: List[int] = None,
) -> pd.DataFrame:
    """Build a feature DataFrame from time-series data.

    Args:
        dates: Sorted list of dates.
        values: Corresponding metric values.
        lag_days: Lag features to create (default: [1, 3, 7, 14]).
        rolling_windows: Rolling mean/std windows (default: [7, 14, 30]).

    Returns:
        DataFrame with features, NaN rows from lag/rolling dropped.
    """
    if lag_days is None:
        lag_days = [1, 3, 7, 14]
    if rolling_windows is None:
        rolling_windows = [7, 14, 30]

    df = pd.DataFrame({"date": dates, "value": values})
    df = df.sort_values("date").reset_index(drop=True)

    # Lag features
    for lag in lag_days:
        df[f"lag_{lag}"] = df["value"].shift(lag)

    # Rolling statistics
    for window in rolling_windows:
        df[f"rolling_mean_{window}"] = df["value"].rolling(window=window).mean()
        df[f"rolling_std_{window}"] = df["value"].rolling(window=window).std()

    # Growth rate (percent change)
    df["growth_1d"] = df["value"].pct_change(1)
    df["growth_7d"] = df["value"].pct_change(7)

    # Day of week and month features
    df["day_of_week"] = pd.to_datetime(df["date"]).dt.dayofweek
    df["month"] = pd.to_datetime(df["date"]).dt.month

    # Drop rows with NaN from lag/rolling
    df = df.dropna().reset_index(drop=True)

    return df


def chronological_split(
    df: pd.DataFrame,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Chronologically split data into train/validation/test sets.

    NEVER randomly shuffles — preserves temporal ordering.
    """
    n = len(df)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))

    train = df.iloc[:train_end].copy()
    val = df.iloc[train_end:val_end].copy()
    test = df.iloc[val_end:].copy()

    logger.info(
        "chronological_split",
        total=n,
        train=len(train),
        val=len(val),
        test=len(test),
    )

    return train, val, test


def get_feature_columns(df: pd.DataFrame) -> List[str]:
    """Get all feature columns (excluding target and date)."""
    exclude = {"date", "value"}
    return [col for col in df.columns if col not in exclude]
