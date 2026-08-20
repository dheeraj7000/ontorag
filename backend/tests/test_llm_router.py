"""Tests for the LLM Router."""

from unittest.mock import patch

from backend.app.core.llm_router import TASK_TIER_FAST, TASK_TIER_SMART, LLMRouter


def test_router_initializes_with_no_keys():
    """Router should work even with no API keys configured."""
    with patch("backend.app.core.llm_router.settings") as mock_settings:
        mock_settings.cerebras_api_key = None
        mock_settings.groq_api_key = None
        mock_settings.together_api_key = None
        mock_settings.ollama_url = "http://localhost:11434"
        mock_settings.ollama_model = "qwen2:0.5b"

        router = LLMRouter()
        assert router.providers[TASK_TIER_FAST] == []
        assert router.providers[TASK_TIER_SMART] == []


def test_router_builds_tiered_providers():
    """Router builds separate fast and smart provider lists."""
    with patch("backend.app.core.llm_router.settings") as mock_settings:
        mock_settings.groq_api_key = "test-groq-key"
        mock_settings.cerebras_api_key = None
        mock_settings.together_api_key = None
        mock_settings.ollama_url = "http://localhost:11434"
        mock_settings.ollama_model = "qwen2:0.5b"

        router = LLMRouter()
        # Groq provides both fast and smart
        assert len(router.providers[TASK_TIER_FAST]) == 1
        assert len(router.providers[TASK_TIER_SMART]) == 1
        assert router.providers[TASK_TIER_FAST][0]["model"] == "openai/gpt-oss-20b"
        assert router.providers[TASK_TIER_SMART][0]["model"] == "openai/gpt-oss-20b"
