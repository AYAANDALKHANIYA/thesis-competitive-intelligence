"""Unit tests for content cleaner."""

from app.services.processing.cleaner import ContentCleaner


class TestContentCleaner:
    def setup_method(self):
        self.cleaner = ContentCleaner()

    def test_cleans_html(self):
        html = "<html><body><p>Hello world this is a test document with enough words to pass validation check threshold and some extra padding words here for safety.</p></body></html>"
        result = self.cleaner.clean(html)
        assert result is not None
        assert "<" not in result
        assert "Hello world" in result

    def test_removes_scripts(self):
        html = "<body><script>alert('x')</script><p>Real content here with sufficient words for the minimum threshold check to pass.</p></body>"
        result = self.cleaner.clean(html)
        assert "alert" not in (result or "")

    def test_returns_none_for_empty(self):
        assert self.cleaner.clean("") is None
        assert self.cleaner.clean("   ") is None

    def test_returns_none_for_too_short(self):
        assert self.cleaner.clean("hello") is None

    def test_normalises_whitespace(self):
        text = "word1    word2\n\n\n\n\nword3 " + " ".join(["padding"] * 20)
        result = self.cleaner.clean(text, is_html=False)
        assert result is not None
        assert "    " not in result

    def test_normalises_unicode(self):
        text = "Smart \u201cquotes\u201d and \u2014 dashes " + " ".join(["word"] * 20)
        result = self.cleaner.clean(text, is_html=False)
        assert result is not None
        assert '"quotes"' in result
