"""Unit tests for sentiment analysis service.

Uses mocked transformers pipeline to avoid downloading real models in CI.
"""

from unittest.mock import patch, MagicMock

from app.services.nlp.sentiment import analyse_sentiment, analyse_batch, LABEL_MAP


class TestLabelMap:
    def test_maps_label_0_to_negative(self):
        assert LABEL_MAP["LABEL_0"] == "negative"

    def test_maps_label_1_to_neutral(self):
        assert LABEL_MAP["LABEL_1"] == "neutral"

    def test_maps_label_2_to_positive(self):
        assert LABEL_MAP["LABEL_2"] == "positive"

    def test_maps_named_labels(self):
        assert LABEL_MAP["positive"] == "positive"
        assert LABEL_MAP["negative"] == "negative"
        assert LABEL_MAP["neutral"] == "neutral"


class TestAnalyseSentiment:
    def _mock_pipeline_result(self, label="LABEL_2", score=0.95):
        """Create a mock pipeline that returns the given label/score."""
        mock_pipe = MagicMock()
        mock_pipe.return_value = [[
            {"label": "LABEL_0", "score": 0.02},
            {"label": "LABEL_1", "score": 0.03},
            {"label": label, "score": score},
        ]]
        return mock_pipe

    @patch("app.services.nlp.sentiment._pipeline", None)
    @patch("app.services.nlp.sentiment._get_pipeline")
    def test_returns_positive(self, mock_get_pipe):
        mock_get_pipe.return_value = self._mock_pipeline_result("LABEL_2", 0.92)
        result = analyse_sentiment("Great product launch!")
        assert result is not None
        assert result["label"] == "positive"
        assert result["score"] == 0.92
        assert result["confidence"] == 0.92

    @patch("app.services.nlp.sentiment._pipeline", None)
    @patch("app.services.nlp.sentiment._get_pipeline")
    def test_returns_negative(self, mock_get_pipe):
        mock_get_pipe.return_value = self._mock_pipeline_result("LABEL_0", 0.88)
        result = analyse_sentiment("Terrible quarter for the company.")
        assert result is not None
        assert result["label"] == "negative"
        assert result["score"] == -0.88
        assert result["confidence"] == 0.88

    @patch("app.services.nlp.sentiment._pipeline", None)
    @patch("app.services.nlp.sentiment._get_pipeline")
    def test_returns_neutral(self, mock_get_pipe):
        mock_get_pipe.return_value = self._mock_pipeline_result("LABEL_1", 0.75)
        result = analyse_sentiment("The company announced its earnings.")
        assert result is not None
        assert result["label"] == "neutral"
        assert result["score"] == 0.0
        assert result["confidence"] == 0.75

    @patch("app.services.nlp.sentiment._get_pipeline")
    def test_returns_none_when_pipeline_unavailable(self, mock_get_pipe):
        mock_get_pipe.return_value = None
        result = analyse_sentiment("Test text")
        assert result is None

    @patch("app.services.nlp.sentiment._get_pipeline")
    def test_returns_none_on_empty_results(self, mock_get_pipe):
        mock_pipe = MagicMock()
        mock_pipe.return_value = []
        mock_get_pipe.return_value = mock_pipe
        result = analyse_sentiment("Test text")
        assert result is None

    @patch("app.services.nlp.sentiment._get_pipeline")
    def test_handles_exception_gracefully(self, mock_get_pipe):
        mock_pipe = MagicMock()
        mock_pipe.side_effect = RuntimeError("Model error")
        mock_get_pipe.return_value = mock_pipe
        result = analyse_sentiment("Test text")
        assert result is None

    @patch("app.services.nlp.sentiment._get_pipeline")
    def test_truncates_long_text(self, mock_get_pipe):
        mock_pipe = self._mock_pipeline_result()
        mock_get_pipe.return_value = mock_pipe
        long_text = "word " * 5000
        analyse_sentiment(long_text)
        # Verify the pipeline received truncated text
        call_args = mock_pipe.call_args[0][0]
        assert len(call_args) <= 2048


class TestAnalyseBatch:
    @patch("app.services.nlp.sentiment._get_pipeline")
    def test_returns_none_list_when_pipeline_unavailable(self, mock_get_pipe):
        mock_get_pipe.return_value = None
        results = analyse_batch(["text1", "text2"])
        assert results == [None, None]

    @patch("app.services.nlp.sentiment._get_pipeline")
    def test_batch_processes_multiple_texts(self, mock_get_pipe):
        mock_pipe = MagicMock()
        mock_pipe.return_value = [
            [{"label": "LABEL_2", "score": 0.9}],
            [{"label": "LABEL_0", "score": 0.85}],
            [{"label": "LABEL_1", "score": 0.80}],
        ]
        mock_get_pipe.return_value = mock_pipe
        results = analyse_batch(["Good text", "Bad text", "Okay text"], batch_size=32)
        assert len(results) == 3
        assert results[0]["label"] == "positive"
        assert results[0]["score"] == 0.9
        assert results[0]["confidence"] == 0.9
        
        assert results[1]["label"] == "negative"
        assert results[1]["score"] == -0.85
        assert results[1]["confidence"] == 0.85
        
        assert results[2]["label"] == "neutral"
        assert results[2]["score"] == 0.0
        assert results[2]["confidence"] == 0.80
