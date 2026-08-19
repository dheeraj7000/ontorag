"""Tests for the LLM Router."""

from unittest.mock import patch

from backend.app.core.llm_router import LLMRouter


def test_router_initializes_with_no_keys():
    """Router should work even with no API keys configured."""
    with patch.dict("os.environ", {
        "CEREBRAS_API_KEY": "",
        "GROQ_API_KEY": "",
        "TOGETHER_API_KEY": "",
    }):
        router = LLMRouter()
        assert router.providers == [] or all(
            p["api_key"] is None or p["api_key"] == ""
            for p in router.providers
        )


def test_router_builds_provider_list():
    """Router builds providers from available API keys."""

    with patch("backend.app.core.llm_router.settings") as mock_settings:
        mock_settings.cerebras_api_key = "test-key"
        mock_settings.groq_api_key = None
        mock_settings.together_api_key = None
        mock_settings.ollama_url = "http://localhost:11434"
        mock_settings.ollama_model = "llama3.1:8b"

        router = LLMRouter()
        assert len(router.providers) == 1
        assert router.providers[0]["name"] == "cerebras"
