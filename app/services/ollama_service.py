from __future__ import annotations

from collections.abc import AsyncIterator

import httpx, os
from fastapi import HTTPException, status
from app.core.config import settings

class OllamaService:
    def __init__(self, base_url: str, model: str, timeout: float) -> None:
        self.base_url = settings.ollama_base_url
        self.model = model
        self.timeout = timeout

    async def chat(self, system_prompt: str, user_prompt: str, response_format: dict | str = "json") -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "format": response_format,
            "options": {
                "temperature": 0.2
            },
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Ollama a mis trop de temps a repondre.",
            ) from exc
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Impossible de joindre Ollama. Verifiez que le service est demarre.",
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Ollama a retourne une erreur HTTP: {exc.response.status_code}",
            ) from exc

        data = response.json()
        return data.get("message", {}).get("content", "").strip()

    async def stream_chat(self, system_prompt: str, user_prompt: str) -> AsyncIterator[str]:
        payload = {
            "model": self.model,
            "stream": True,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        yield f"{line}\n"
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Le streaming Ollama a depasse le delai autorise.",
            ) from exc
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Impossible de joindre Ollama pour le streaming.",
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Ollama a retourne une erreur HTTP: {exc.response.status_code}",
            ) from exc
