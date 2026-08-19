"""
LLM Router — two-tier routing for cost/quality optimization.

Tier 1 (Fast/Cheap): Llama 3.1 8B on Groq — extraction, simple JSON tasks
Tier 2 (Smart): GPT-OSS 20B on Groq — reasoning, answer generation, hallucination detection

Fallback: Ollama (local, unlimited, no internet needed)
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

import aiohttp

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

# Task complexity tiers
TASK_TIER_FAST = "fast"  # Extraction, simple JSON output
TASK_TIER_SMART = "smart"  # Reasoning, answer generation, hallucination


class LLMRouter:
    """Two-tier LLM router: fast model for extraction, smart model for reasoning."""

    def __init__(self):
        self.providers = self._build_provider_list()
        self.ollama_url = f"{settings.ollama_url}/api/generate"
        self._last_call_time: Dict[str, float] = {}

    def _build_provider_list(self) -> Dict[str, List[Dict[str, Any]]]:
        """Build provider lists for each tier."""
        fast_providers = []
        smart_providers = []

        if settings.groq_api_key:
            # Tier 1: Fast/cheap for extraction
            fast_providers.append({
                "name": "groq-fast",
                "base_url": "https://api.groq.com/openai/v1",
                "api_key": settings.groq_api_key,
                "model": "llama-3.1-8b-instant",
                "max_rpm": 30,
                "min_interval": 2.0,
            })
            # Tier 2: Smart for reasoning
            smart_providers.append({
                "name": "groq-smart",
                "base_url": "https://api.groq.com/openai/v1",
                "api_key": settings.groq_api_key,
                "model": "gpt-oss-20b",
                "max_rpm": 15,
                "min_interval": 4.0,
            })

        if settings.cerebras_api_key:
            # Cerebras as additional option for both tiers
            cerebras_config = {
                "name": "cerebras",
                "base_url": "https://api.cerebras.ai/v1",
                "api_key": settings.cerebras_api_key,
                "model": "gemma-4-31b",
                "max_rpm": 5,
                "min_interval": 12.0,
            }
            fast_providers.append(cerebras_config)
            smart_providers.append(cerebras_config)

        if settings.together_api_key:
            together_config = {
                "name": "together",
                "base_url": "https://api.together.xyz/v1",
                "api_key": settings.together_api_key,
                "model": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
                "max_rpm": 10,
                "min_interval": 6.0,
            }
            smart_providers.append(together_config)

        return {
            TASK_TIER_FAST: fast_providers,
            TASK_TIER_SMART: smart_providers,
        }

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        json_mode: bool = True,
        max_tokens: int = 2048,
        tier: str = TASK_TIER_FAST,
    ) -> Dict[str, Any]:
        """
        Generate a response using the appropriate tier.

        tier="fast" → Llama 3.1 8B (extraction, JSON tasks)
        tier="smart" → GPT-OSS 20B (reasoning, answers, hallucination)
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Get providers for the requested tier
        providers = self.providers.get(tier, self.providers[TASK_TIER_FAST])

        # Try each provider in order
        for provider in providers:
            try:
                result = await self._call_provider(
                    provider, messages, temperature, json_mode, max_tokens
                )
                if result is not None:
                    return {
                        "provider": f"{provider['name']} ({provider['model']})",
                        "response": result,
                    }
            except Exception as e:
                logger.warning(f"Provider {provider['name']} failed: {e}")
                continue

        # Fallback to Ollama
        logger.info(f"All {tier} providers failed, falling back to Ollama")
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
                        raise RuntimeError(
                            f"Ollama returned {resp.status}: {body[:200]}"
                        )

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
