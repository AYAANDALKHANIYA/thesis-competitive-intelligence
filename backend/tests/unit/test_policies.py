"""Unit tests for freshness policies."""

from datetime import datetime, timedelta, timezone

from app.services.ingestion.policies import FreshnessPolicy


class TestFreshnessPolicy:
    def setup_method(self):
        self.policy = FreshnessPolicy()

    def test_fresh_source(self):
        """Recently checked source should be fresh."""
        last_checked = datetime.now(timezone.utc) - timedelta(minutes=5)
        assert self.policy.is_fresh("rss", last_checked_at=last_checked)

    def test_stale_source(self):
        """Old check time should not be fresh."""
        last_checked = datetime.now(timezone.utc) - timedelta(days=2)
        assert not self.policy.is_fresh("rss", last_checked_at=last_checked)

    def test_next_check_at_override(self):
        """next_check_at in the future should be fresh."""
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        assert self.policy.is_fresh("website", next_check_at=future)

    def test_never_checked(self):
        """Source never checked should not be fresh."""
        assert not self.policy.is_fresh("website")

    def test_next_check_time(self):
        next_time = self.policy.next_check_time("rss")
        assert next_time > datetime.now(timezone.utc)
