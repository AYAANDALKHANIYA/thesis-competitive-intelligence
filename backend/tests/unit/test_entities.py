"""Unit tests for entity extraction service.

Uses mocked spaCy to avoid downloading models in CI.
"""

from unittest.mock import patch, MagicMock

from app.services.nlp.entities import extract_entities, extract_batch, ENTITY_TYPES


class TestEntityTypes:
    def test_includes_expected_types(self):
        assert "ORG" in ENTITY_TYPES
        assert "PERSON" in ENTITY_TYPES
        assert "GPE" in ENTITY_TYPES
        assert "PRODUCT" in ENTITY_TYPES
        assert "LOC" in ENTITY_TYPES


class MockEnt:
    """Minimal mock of a spaCy entity span."""

    def __init__(self, text: str, label: str, start: int = 0, end: int = 5):
        self.text = text
        self.label_ = label
        self.start_char = start
        self.end_char = end


class TestExtractEntities:
    def _mock_nlp(self, ents):
        """Create a mock NLP model returning given entities."""
        mock_doc = MagicMock()
        mock_doc.ents = [MockEnt(*e) if isinstance(e, tuple) else e for e in ents]
        mock_model = MagicMock()
        mock_model.return_value = mock_doc
        return mock_model

    @patch("app.services.nlp.entities._get_nlp")
    def test_extracts_org_entities(self, mock_get_nlp):
        mock_get_nlp.return_value = self._mock_nlp([
            ("Microsoft", "ORG", 0, 9),
            ("Google", "ORG", 20, 26),
        ])
        results = extract_entities("Microsoft competes with Google.")
        assert len(results) == 2
        assert results[0]["entity_text"] == "Microsoft"
        assert results[0]["entity_type"] == "ORG"

    @patch("app.services.nlp.entities._get_nlp")
    def test_filters_unwanted_types(self, mock_get_nlp):
        mock_get_nlp.return_value = self._mock_nlp([
            ("100", "CARDINAL", 0, 3),  # Not in ENTITY_TYPES
            ("Apple", "ORG", 10, 15),
        ])
        results = extract_entities("100 units from Apple.")
        assert len(results) == 1
        assert results[0]["entity_type"] == "ORG"

    @patch("app.services.nlp.entities._get_nlp")
    def test_deduplicates_entities(self, mock_get_nlp):
        mock_get_nlp.return_value = self._mock_nlp([
            ("Apple", "ORG", 0, 5),
            ("Apple", "ORG", 20, 25),  # Duplicate
        ])
        results = extract_entities("Apple announced. Apple reported.")
        assert len(results) == 1

    @patch("app.services.nlp.entities._get_nlp")
    def test_returns_empty_when_nlp_unavailable(self, mock_get_nlp):
        mock_get_nlp.return_value = None
        results = extract_entities("Some text about companies.")
        assert results == []

    @patch("app.services.nlp.entities._get_nlp")
    def test_handles_exception_gracefully(self, mock_get_nlp):
        mock_model = MagicMock()
        mock_model.side_effect = RuntimeError("Model error")
        mock_get_nlp.return_value = mock_model
        results = extract_entities("Some text")
        assert results == []

    @patch("app.services.nlp.entities._get_nlp")
    def test_result_contains_positions(self, mock_get_nlp):
        mock_get_nlp.return_value = self._mock_nlp([
            ("Tesla", "ORG", 10, 15),
        ])
        results = extract_entities("Bought a Tesla Model 3.")
        assert results[0]["start_position"] == 10
        assert results[0]["end_position"] == 15
        assert results[0]["confidence"] is None


class TestExtractBatch:
    @patch("app.services.nlp.entities._get_nlp")
    def test_returns_empty_lists_when_unavailable(self, mock_get_nlp):
        mock_get_nlp.return_value = None
        results = extract_batch(["text1", "text2"])
        assert results == [[], []]

    @patch("app.services.nlp.entities.extract_entities")
    @patch("app.services.nlp.entities._get_nlp")
    def test_processes_batch(self, mock_get_nlp, mock_extract):
        mock_get_nlp.return_value = MagicMock()
        mock_extract.return_value = [{"entity_text": "Test", "entity_type": "ORG"}]
        results = extract_batch(["text1"])
        assert len(results) == 1
