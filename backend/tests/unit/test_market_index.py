"""Unit tests for the Market Activity Index calculation.

Tests the normalisation logic and weight application without database access.
"""

import pytest


class TestMarketIndexNormalisation:
    """Pure-logic tests for the MAI calculation rules."""

    def _normalise_news_volume(self, doc_count: int, period_days: int = 30) -> float:
        """Replicate the normalisation in MarketActivityIndexService.calculate."""
        return min(1.0, doc_count / max(period_days, 1))

    def _normalise_sentiment(self, avg_sentiment: float) -> float:
        """Map [-1, 1] → [0, 1]."""
        return max(0.0, min(1.0, (avg_sentiment + 1) / 2))

    def _normalise_content_activity(self, doc_count: int, period_days: int = 30) -> float:
        docs_per_day = doc_count / max(period_days, 1)
        return min(1.0, docs_per_day / 5.0)

    def _calculate_index(self, components: dict, weights: dict) -> float:
        index_value = sum(components[key] * weights[key] for key in weights)
        return round(min(1.0, max(0.0, index_value)) * 100, 2)

    # ── News volume normalisation ──────────────────────────────────────

    def test_news_volume_zero_docs(self):
        assert self._normalise_news_volume(0) == 0.0

    def test_news_volume_moderate(self):
        # 15 docs in 30 days → 0.5
        assert self._normalise_news_volume(15) == 0.5

    def test_news_volume_caps_at_one(self):
        # 100 docs in 30 days → capped at 1.0
        assert self._normalise_news_volume(100) == 1.0

    # ── Sentiment normalisation ────────────────────────────────────────

    def test_sentiment_positive(self):
        # avg_sentiment = 1.0 → (1+1)/2 = 1.0
        assert self._normalise_sentiment(1.0) == 1.0

    def test_sentiment_negative(self):
        # avg_sentiment = -1.0 → (-1+1)/2 = 0.0
        assert self._normalise_sentiment(-1.0) == 0.0

    def test_sentiment_neutral(self):
        # avg_sentiment = 0.0 → (0+1)/2 = 0.5
        assert self._normalise_sentiment(0.0) == 0.5

    def test_sentiment_clamps_above(self):
        assert self._normalise_sentiment(5.0) == 1.0

    def test_sentiment_clamps_below(self):
        assert self._normalise_sentiment(-5.0) == 0.0

    def test_negative_vs_positive_polarity_moves_opposite(self):
        # positive confidence 0.95 -> polarity +0.95
        pos_norm = self._normalise_sentiment(0.95)
        # negative confidence 0.95 -> polarity -0.95
        neg_norm = self._normalise_sentiment(-0.95)
        
        # Neutral baseline is 0.5.
        neutral_norm = self._normalise_sentiment(0.0)
        
        assert pos_norm > neutral_norm
        assert neg_norm < neutral_norm
        
        assert pos_norm == pytest.approx(0.975)
        assert neg_norm == pytest.approx(0.025)

    # ── Content activity normalisation ─────────────────────────────────

    def test_content_activity_zero(self):
        assert self._normalise_content_activity(0) == 0.0

    def test_content_activity_high(self):
        # 150 docs / 30 days = 5/day → 5/5 = 1.0
        assert self._normalise_content_activity(150) == 1.0

    def test_content_activity_caps(self):
        # Way above cap
        assert self._normalise_content_activity(1000) == 1.0

    # ── Weighted index ─────────────────────────────────────────────────

    def test_all_zero_components(self):
        components = {
            "news_volume": 0.0,
            "sentiment": 0.0,
            "topic_momentum": 0.0,
            "competitor_activity": 0.0,
            "content_activity": 0.0,
        }
        weights = {
            "news_volume": 0.25,
            "sentiment": 0.20,
            "topic_momentum": 0.20,
            "competitor_activity": 0.20,
            "content_activity": 0.15,
        }
        assert self._calculate_index(components, weights) == 0.0

    def test_all_max_components(self):
        components = {k: 1.0 for k in [
            "news_volume", "sentiment", "topic_momentum",
            "competitor_activity", "content_activity",
        ]}
        weights = {
            "news_volume": 0.25,
            "sentiment": 0.20,
            "topic_momentum": 0.20,
            "competitor_activity": 0.20,
            "content_activity": 0.15,
        }
        assert self._calculate_index(components, weights) == 100.0

    def test_index_caps_at_100(self):
        components = {k: 2.0 for k in [
            "news_volume", "sentiment", "topic_momentum",
            "competitor_activity", "content_activity",
        ]}
        weights = {
            "news_volume": 0.25,
            "sentiment": 0.20,
            "topic_momentum": 0.20,
            "competitor_activity": 0.20,
            "content_activity": 0.15,
        }
        assert self._calculate_index(components, weights) == 100.0

    def test_partial_components(self):
        components = {
            "news_volume": 0.5,
            "sentiment": 0.5,
            "topic_momentum": 0.0,
            "competitor_activity": 0.5,
            "content_activity": 0.0,
        }
        weights = {
            "news_volume": 0.25,
            "sentiment": 0.20,
            "topic_momentum": 0.20,
            "competitor_activity": 0.20,
            "content_activity": 0.15,
        }
        expected = (0.5*0.25 + 0.5*0.20 + 0*0.20 + 0.5*0.20 + 0*0.15) * 100
        assert self._calculate_index(components, weights) == round(expected, 2)
