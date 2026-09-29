"""Unit tests for feature engineering."""

from datetime import date, timedelta

from app.services.prediction.features import build_features, chronological_split


class TestFeatureEngineering:
    def test_build_features_creates_lags(self):
        dates = [date.today() - timedelta(days=i) for i in range(60, 0, -1)]
        values = [float(i) for i in range(60)]
        df = build_features(dates, values)
        assert "lag_1" in df.columns
        assert "lag_7" in df.columns
        assert "rolling_mean_7" in df.columns
        assert len(df) > 0

    def test_chronological_split_preserves_order(self):
        dates = [date.today() - timedelta(days=i) for i in range(100, 0, -1)]
        values = [float(i) for i in range(100)]
        df = build_features(dates, values)
        train, val, test = chronological_split(df)
        assert len(train) > 0
        assert len(val) > 0
        assert len(test) > 0
        # Train dates should be before val dates
        assert train["date"].iloc[-1] <= val["date"].iloc[0]

    def test_growth_features(self):
        dates = [date.today() - timedelta(days=i) for i in range(60, 0, -1)]
        values = [float(i) * 1.5 for i in range(60)]
        df = build_features(dates, values)
        assert "growth_1d" in df.columns
        assert "growth_7d" in df.columns
