"""Unit tests for URL normalisation and content hashing."""

from app.services.extraction.base import content_hash, normalise_url


class TestNormaliseUrl:
    def test_strips_fragment(self):
        assert normalise_url("https://example.com/page#section") == "https://example.com/page"

    def test_lowercases_scheme_and_host(self):
        assert normalise_url("HTTPS://Example.COM/Path") == "https://example.com/Path"

    def test_strips_trailing_slash(self):
        assert normalise_url("https://example.com/page/") == "https://example.com/page"

    def test_root_path_preserved(self):
        assert normalise_url("https://example.com") == "https://example.com/"

    def test_preserves_query(self):
        assert normalise_url("https://example.com/page?q=1") == "https://example.com/page?q=1"


class TestContentHash:
    def test_deterministic(self):
        assert content_hash("hello world") == content_hash("hello world")

    def test_whitespace_normalised(self):
        assert content_hash("hello   world") == content_hash("hello world")

    def test_different_content_different_hash(self):
        assert content_hash("hello") != content_hash("world")
