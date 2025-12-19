import httpx
from typing import Dict
from ..schemas import LLMRequest, LLMResponse
from ...core.config import settings

class OpenAIAdapter:
    """OpenAI API adapter with scoped token injection"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url="https://api.openai.com/v1",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            timeout=settings.inference_timeout_seconds
        )
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        payload = {
            "model": request.model,
            "messages": [{"role": "user", "content": request.prompt}],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "user": request.user_id  # For OpenAI user tracking
        }
        
        response = await self.client.post("/chat/completions", json=payload)
        response.raise_for_status()
        
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        
        return LLMResponse(
            content=content,
            model=request.model,
            tokens_used=data["usage"]["total_tokens"],
            latency_ms=response.elapsed.total_seconds() * 1000
        )