"""
LLM Router — tries free APIs in priority order, falls back to local Ollama.

Provider priority:
1. Cerebras (Llama 3.1 70B) — unlimited free, 30 req/min
2. Groq (Mixtral 8x7B) — $5/mo credits, 20 req/min
3. Together AI (Llama 3.1 70B) — $5 signup credit
4. Ollama (local Llama 3.1 8B) — truly unlimited, no internet
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

import aiohttp

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class LLMRouter:
    """Routes LLM calls through free providers with automatic fallback."""

    def __init__(self):
        self.providers = self._build_provider_list()
        self.ollama_url = f"{settings.ollama_url}/api/generate"
        self._last_call_time: Dict[str, float] = {}

    def _build_provider_list(self) -> List[Dict[str, Any]]:
        """Build ordered list of available providers."""
        providers = []

        if settings.cerebras_api_key:
            providers.append({
                "name": "cerebras",
                "base_url": "https://api.cerebras.ai/v1",
                "api_key": settings.cerebras_api_key,
                "model": "llama3.1-70b",
                "max_rpm": 5,
                "min_interval": 12.0,  # 5 req/min = 12s between requests
            })

        if settings.groq_api_key:
            providers.append({
                "name": "groq",
                "base_url": "https://api.groq.com/openai/v1",
                "api_key": settings.groq_api_key,
                "model": "mixtral-8x7b-32768",
                "max_rpm": 20,
                "min_interval": 3.0,
            })

        if settings.together_api_key:
            providers.append({
                "name": "together",
                "base_url": "https://api.together.xyz/v1",
                "api_key": settings.together_api_key,
                "model": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
                "max_rpm": 10,
                "min_interval": 6.0,
            })

        return providers

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        json_mode: bool = True,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """
        Generate a response from the best available provider.

        Returns dict with keys: provider, response, usage
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Try each cloud provider in priority order
        for provider in self.providers:
            try:
                result = await self._call_provider(
                    provider, messages, temperature, json_mode, max_tokens
                )
                if result is not None:
                    return {
                        "provider": provider["name"],
                        "response": result,
                    }
            except Exception as e:
                logger.warning(f"Provider {provider['name']} failed: {e}")
                continue

        # Fallback to Ollama
        logger.info("All cloud providers failed, falling back to Ollama")
        return await self._call_ollama(prompt, system_prompt, json_mode)

    async def _call_provider(
        self,
        provider: Dict[str, Any],
        messages: List[Dict[str, str]],
        temperature: float,
        json_mode: bool,
        max_tokens: int,
    ) -> Optional[Any]:
        """Call a provider's OpenAI-compatible chat completions endpoint."""
        name = provider["name"]

        # Simple rate limiting
        now = time.time()
        last = self._last_call_time.get(name, 0)
        wait = provider["min_interval"] - (now - last)
        if wait > 0:
            import asyncio
            await asyncio.sleep(wait)

        headers = {
            "Authorization": f"Bearer {provider['api_key']}",
            "Content-Type": "application/json",
        }

        payload: Dict[str, Any] = {
            "model": provider["model"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        timeout = aiohttp.ClientTimeout(total=60)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            url = f"{provider['base_url']}/chat/completions"
            async with session.post(url, headers=headers, json=payload) as resp:
                self._last_call_time[name] = time.time()

                if resp.status != 200:
                    body = await resp.text()
                    raise RuntimeError(
                        f"{name} returned {resp.status}: {body[:200]}"
                    )

                data = await resp.json()
                content = data["choices"][0]["message"]["content"]

                if json_mode:
                    return json.loads(content)
                return content

    async def _call_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str],
        json_mode: bool,
    ) -> Dict[str, Any]:
        """Fallback to local Ollama instance."""
        payload: Dict[str, Any] = {
            "model": settings.ollama_model,
            "prompt": prompt,
            "stream": False,
        }
        if system_prompt:
            payload["system"] = system_prompt
        if json_mode:
            payload["format"] = "json"

        timeout = aiohttp.ClientTimeout(total=120)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(self.ollama_url, json=payload) as resp:
                    if resp.status != 200:
                        body = await resp.text()
                        raise RuntimeError(f"Ollama returned {resp.status}: {body[:200]}")

                    data = await resp.json()
                    response_text = data.get("response", "")

                    if json_mode:
                        return {
                            "provider": "ollama",
                            "response": json.loads(response_text),
                        }
                    return {
                        "provider": "ollama",
                        "response": response_text,
                    }
        except aiohttp.ClientConnectorError:
            raise RuntimeError(
                "Ollama is not running. Start it with: ollama serve"
            )


# Singleton instance
llm_router = LLMRouter()
