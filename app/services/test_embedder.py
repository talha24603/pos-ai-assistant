import unittest
from unittest.mock import patch, MagicMock
from app.services.embedder import create_embedding
from app.config import settings


class TestEmbedder(unittest.TestCase):
    def test_create_embedding_missing_api_key(self):
        """Test that a graceful dummy vector is returned when OPENROUTER_API_KEY is not configured."""
        with patch("app.services.embedder.OPENROUTER_API_KEY", None):
            embedding = create_embedding("Hello world")
            self.assertIsInstance(embedding, list)
            self.assertEqual(len(embedding), 384)
            self.assertTrue(all(val == 0.0 for val in embedding))

    @patch("httpx.Client")
    def test_create_embedding_mocked_success(self, mock_client_class):
        """Test standard success response from OpenRouter Embeddings API via mock."""
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "object": "list",
            "data": [
                {
                    "object": "embedding",
                    "index": 0,
                    "embedding": [0.1, 0.2, 0.3, 0.4]
                }
            ],
            "model": "openai/text-embedding-3-small",
            "usage": {
                "prompt_tokens": 2,
                "total_tokens": 2
            }
        }
        mock_client.post.return_value = mock_response

        # Force a dummy API key for testing
        with patch("app.services.embedder.OPENROUTER_API_KEY", "dummy-key"):
            embedding = create_embedding("Hello world")

            # Assert correct HTTP call details
            mock_client.post.assert_called_once_with(
                "https://openrouter.ai/api/v1/embeddings",
                headers={
                    "Authorization": "Bearer dummy-key",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "openai/text-embedding-3-small",
                    "input": "Hello world",
                    "dimensions": 384
                }
            )

            # Assert parsed response matches
            self.assertEqual(embedding, [0.1, 0.2, 0.3, 0.4])

    def test_create_embedding_integration(self):
        """Integration test that runs against the live OpenRouter API if a key is present."""
        if not settings.OPENROUTER_API_KEY:
            self.skipTest(
                "OPENROUTER_API_KEY environment variable not set; skipping integration test."
            )

        text_to_embed = "Test sentence for POS AI Assistant RAG embedding service"
        embedding = create_embedding(text_to_embed)

        self.assertIsInstance(embedding, list)
        self.assertEqual(len(embedding), settings.EMBEDDING_DIMENSION)
        self.assertTrue(all(isinstance(val, float) for val in embedding))
        print(
            f"\n[Integration Test Success] Generated vector with "
            f"{len(embedding)} dimensions successfully."
        )


if __name__ == "__main__":
    unittest.main()
