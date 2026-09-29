"""Unit tests for normalizer."""

from datetime import timezone

from app.services.processing.normalizer import ContentNormalizer


class TestContentNormalizer:
    def setup_method(self):
        self.normalizer = ContentNormalizer()

    def test_count_words(self):
        assert self.normalizer.count_words("hello world foo") == 3
        assert self.normalizer.count_words("") == 0

    def test_is_valid_content_sufficient(self):
        text = " ".join(f"word{i}" for i in range(25))
        assert self.normalizer.is_valid_content(text)

    def test_is_valid_content_too_short(self):
        assert not self.normalizer.is_valid_content("short")

    def test_is_valid_content_repetitive(self):
        text = "nav " * 100
        assert not self.normalizer.is_valid_content(text)

    def test_normalise_date_iso(self):
        dt = self.normalizer.normalise_date("2024-01-15")
        assert dt is not None
        assert dt.day == 15

    def test_normalise_date_none(self):
        assert self.normalizer.normalise_date(None) is None
        assert self.normalizer.normalise_date("not a date") is None
