"""
Deduplication service — exact hash + near-duplicate detection using SimHash.
"""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from typing import Optional, Set


class SimHash:
    """SimHash for near-duplicate detection."""

    def __init__(self, bits: int = 64) -> None:
        self.bits = bits

    def compute(self, text: str) -> int:
        """Compute SimHash of text."""
        tokens = self._tokenize(text)
        if not tokens:
            return 0

        v = [0] * self.bits
        for token in tokens:
            token_hash = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            for i in range(self.bits):
                bit = (token_hash >> i) & 1
                v[i] += 1 if bit else -1

        fingerprint = 0
        for i in range(self.bits):
            if v[i] > 0:
                fingerprint |= 1 << i
        return fingerprint

    def hamming_distance(self, hash1: int, hash2: int) -> int:
        """Calculate Hamming distance between two hashes."""
        return bin(hash1 ^ hash2).count("1")

    def is_near_duplicate(
        self, hash1: int, hash2: int, threshold: int = 3
    ) -> bool:
        """Check if two documents are near-duplicates."""
        return self.hamming_distance(hash1, hash2) <= threshold

    def _tokenize(self, text: str) -> list[str]:
        """Simple word tokenization."""
        text = text.lower()
        text = re.sub(r"[^\w\s]", "", text)
        words = text.split()
        # Generate 3-grams for better accuracy
        ngrams = []
        for i in range(len(words) - 2):
            ngrams.append(" ".join(words[i : i + 3]))
        return ngrams if ngrams else words


class Deduplicator:
    """Detects and prevents duplicate documents."""

    def __init__(self) -> None:
        self._simhash = SimHash()
        self._seen_hashes: Set[str] = set()
        self._simhash_cache: dict[str, int] = {}

    def exact_hash(self, content: str) -> str:
        """SHA-256 hash of whitespace-normalised content."""
        normalised = " ".join(content.split())
        return hashlib.sha256(normalised.encode("utf-8")).hexdigest()

    def is_exact_duplicate(self, content_hash: str) -> bool:
        """Check if an exact hash has been seen."""
        return content_hash in self._seen_hashes

    def register_hash(self, content_hash: str) -> None:
        """Register a hash as seen."""
        self._seen_hashes.add(content_hash)

    def compute_simhash(self, content: str) -> int:
        """Compute SimHash for near-duplicate detection."""
        return self._simhash.compute(content)

    def is_near_duplicate(
        self, content: str, existing_hashes: list[int], threshold: int = 3
    ) -> bool:
        """Check if content is a near-duplicate of any existing document."""
        new_hash = self._simhash.compute(content)
        for existing in existing_hashes:
            if self._simhash.is_near_duplicate(new_hash, existing, threshold):
                return True
        return False
