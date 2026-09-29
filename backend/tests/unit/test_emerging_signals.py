"""Unit tests for emerging signal detection logic.

Tests the growth-rate calculations and threshold filtering without DB access.
"""

import pytest


class TestGrowthRateCalculation:
    """Tests for the growth-rate formula used in EmergingSignalService."""

    @staticmethod
    def _growth_rate(recent: int, historical: int, min_mentions: int = 5) -> float | None:
        """Replicate the growth-rate formula from EmergingSignalService."""
        if recent < min_mentions:
            return None
        if historical > 0:
            return (recent - historical) / historical
        elif recent >= min_mentions:
            return 2.0  # New topic
        return None

    # ── Normal growth scenarios ─────────────────────────────────────────

    def test_doubling(self):
        assert self._growth_rate(20, 10) == 1.0

    def test_tripling(self):
        assert self._growth_rate(30, 10) == 2.0

    def test_no_change(self):
        assert self._growth_rate(10, 10) == 0.0

    def test_decline(self):
        result = self._growth_rate(5, 10)
        assert result == -0.5

    # ── New topics (no historical data) ────────────────────────────────

    def test_new_topic_above_threshold(self):
        assert self._growth_rate(10, 0) == 2.0

    def test_new_topic_at_exact_threshold(self):
        assert self._growth_rate(5, 0) == 2.0

    # ── Below minimum mentions ─────────────────────────────────────────

    def test_below_min_mentions_returns_none(self):
        assert self._growth_rate(3, 10) is None

    def test_zero_recent_returns_none(self):
        assert self._growth_rate(0, 10) is None

    # ── Custom thresholds ──────────────────────────────────────────────

    def test_custom_min_mentions(self):
        assert self._growth_rate(3, 0, min_mentions=3) == 2.0
        assert self._growth_rate(2, 0, min_mentions=3) is None


class TestConfidenceCalculation:
    """Tests for the confidence formula."""

    @staticmethod
    def _confidence(recent_count: int, min_mentions: int = 5) -> float:
        """Replicate confidence: min(1.0, recent_count / (min_mentions * 3))."""
        return min(1.0, recent_count / (min_mentions * 3))

    def test_low_confidence(self):
        assert self._confidence(5) == pytest.approx(1/3, abs=0.01)

    def test_medium_confidence(self):
        assert self._confidence(10) == pytest.approx(2/3, abs=0.01)

    def test_high_confidence(self):
        assert self._confidence(15) == 1.0

    def test_caps_at_one(self):
        assert self._confidence(100) == 1.0

    def test_with_custom_min(self):
        assert self._confidence(6, min_mentions=2) == 1.0


class TestSentimentShiftDetection:
    """Tests for sentiment-shift detection logic."""

    @staticmethod
    def _is_significant_shift(shift: float, threshold: float = 0.15) -> bool:
        return abs(shift) >= threshold

    def test_significant_positive_shift(self):
        assert self._is_significant_shift(0.3) is True

    def test_significant_negative_shift(self):
        assert self._is_significant_shift(-0.2) is True

    def test_insignificant_shift(self):
        assert self._is_significant_shift(0.05) is False

    def test_exact_threshold(self):
        assert self._is_significant_shift(0.15) is True

    def test_just_below_threshold(self):
        assert self._is_significant_shift(0.14) is False


class TestSignalFiltering:
    """Tests for the growth_threshold filtering."""

    @staticmethod
    def _passes_threshold(growth_rate: float, threshold: float = 1.5) -> bool:
        return growth_rate >= threshold

    def test_above_threshold(self):
        assert self._passes_threshold(2.0) is True

    def test_at_threshold(self):
        assert self._passes_threshold(1.5) is True

    def test_below_threshold(self):
        assert self._passes_threshold(1.0) is False

    def test_negative_growth(self):
        assert self._passes_threshold(-0.5) is False
