"""Unit tests for URL normalisation utility.

The normalise_url function is in app.services.extraction.base and is
already tested in test_hashing.py, but these tests cover additional edge cases.
"""

from app.services.extraction.base import normalise_url


class TestUrlNormalisation:
    """Extended edge-case tests for normalise_url."""

    def test_basic_normalisation(self):
        assert normalise_url("https://example.com/page") == "https://example.com/page"

    def test_strips_fragment(self):
        assert normalise_url("https://example.com/page#section") == "https://example.com/page"

    def test_lowercases_scheme(self):
        assert normalise_url("HTTPS://example.com/page") == "https://example.com/page"

    def test_lowercases_host(self):
        assert normalise_url("https://EXAMPLE.COM/page") == "https://example.com/page"

    def test_preserves_path_case(self):
        # Path case should be preserved (paths are case-sensitive)
        assert normalise_url("https://example.com/Page") == "https://example.com/Page"

    def test_strips_trailing_slash_on_path(self):
        assert normalise_url("https://example.com/page/") == "https://example.com/page"

    def test_root_path_gets_slash(self):
        assert normalise_url("https://example.com") == "https://example.com/"

    def test_preserves_query_parameters(self):
        assert normalise_url("https://example.com/search?q=test&page=1") == \
            "https://example.com/search?q=test&page=1"

    def test_strips_fragment_preserves_query(self):
        assert normalise_url("https://example.com/page?q=1#frag") == \
            "https://example.com/page?q=1"

    def test_complex_url(self):
        url = "HTTPS://WWW.Example.COM/a/b/c/?foo=bar#section"
        expected = "https://www.example.com/a/b/c?foo=bar"
        assert normalise_url(url) == expected

    def test_url_with_port(self):
        assert normalise_url("http://example.com:8080/page") == \
            "http://example.com:8080/page"

    def test_url_with_auth(self):
        assert normalise_url("https://user:pass@EXAMPLE.COM/path") == \
            "https://user:pass@example.com/path"

    def test_unicode_path(self):
        url = "https://example.com/日本語"
        result = normalise_url(url)
        assert "example.com" in result

    def test_empty_query_string(self):
        result = normalise_url("https://example.com/page?")
        assert "example.com" in result

    def test_multiple_slashes_in_path(self):
        # Multiple slashes are preserved in the path
        result = normalise_url("https://example.com/a//b")
        assert "/a//b" in result
