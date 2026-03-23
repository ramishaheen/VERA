"""
Python client for the VERA API.
"""

import requests
from typing import List, Dict, Any, Optional


class VERAClient:
    """Client for interacting with the VERA REST API."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: int = 60,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def chat_completions(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> Dict[str, Any]:
        """Send a chat completion request (OpenAI-compatible)."""
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        response = self.session.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def vera_process(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o-mini",
    ) -> Dict[str, Any]:
        """Send a request to VERA's detailed processing endpoint."""
        payload = {"model": model, "messages": messages}
        response = self.session.post(
            f"{self.base_url}/vera/process",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def configure(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update VERA's LLM configuration."""
        payload = {}
        if api_key:
            payload["api_key"] = api_key
        if model:
            payload["model"] = model
        if base_url:
            payload["base_url"] = base_url
        response = self.session.post(
            f"{self.base_url}/api/configure",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def health_check(self) -> Dict[str, Any]:
        """Check if VERA server is healthy."""
        response = self.session.get(f"{self.base_url}/health", timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def list_models(self) -> Dict[str, Any]:
        """List available models."""
        response = self.session.get(f"{self.base_url}/v1/models", timeout=self.timeout)
        response.raise_for_status()
        return response.json()


def process_with_vera(
    prompt: str,
    base_url: str = "http://localhost:8000",
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Convenience function to process a single prompt through VERA."""
    client = VERAClient(base_url=base_url, api_key=api_key)
    return client.vera_process([{"role": "user", "content": prompt}])
