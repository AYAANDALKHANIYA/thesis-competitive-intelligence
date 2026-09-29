"""Unit tests for deduplicator."""

from app.services.processing.deduplicator import Deduplicator


class TestDeduplicator:
    def setup_method(self):
        self.dedup = Deduplicator()

    def test_exact_hash_deterministic(self):
        h1 = self.dedup.exact_hash("hello world")
        h2 = self.dedup.exact_hash("hello world")
        assert h1 == h2

    def test_exact_hash_whitespace_normalised(self):
        h1 = self.dedup.exact_hash("hello  world")
        h2 = self.dedup.exact_hash("hello world")
        assert h1 == h2

    def test_is_exact_duplicate(self):
        h = self.dedup.exact_hash("test content")
        self.dedup.register_hash(h)
        assert self.dedup.is_exact_duplicate(h)

    def test_not_duplicate(self):
        assert not self.dedup.is_exact_duplicate("nonexistent")

    def test_simhash_similar(self):
        text1 = "The quick brown fox jumps over the lazy dog in the park"
        text2 = "The quick brown fox leaps over the lazy dog in the garden"
        hash1 = self.dedup.compute_simhash(text1)
        hash2 = self.dedup.compute_simhash(text2)
        # Similar texts should have close hashes
        assert hash1 != 0
        assert hash2 != 0

    def test_simhash_different(self):
        text1 = "The economy is growing fast with new technology investments worldwide"
        text2 = "Cooking recipes for holiday parties are very popular this season fall"
        hash1 = self.dedup.compute_simhash(text1)
        hash2 = self.dedup.compute_simhash(text2)
        assert hash1 != hash2
