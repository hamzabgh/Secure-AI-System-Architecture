import ollama
from typing import Dict
from ..schemas import LLMRequest, LLMResponse
from ...core.config import settings
import time
class OllamaAdapter:
    """Ollama local model adapter"""
    
    def __init__(self):
        self.client = ollama.AsyncClient(host=settings.ollama_base_url)
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        # Map model names
        model_map = {
            "llama2": "llama2:latest",
            "mistral": "mistral:latest",
            "phi": "phi:latest",
        }
        ollama_model = model_map.get(request.model, request.model)
        
        start_time = time.time()
        response = await self.client.chat(
            model=ollama_model,
            messages=[{"role": "user", "content": request.prompt}],
            options={
                "temperature": request.temperature,
                "num_predict": request.max_tokens
            }
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        return LLMResponse(
            content=response["message"]["content"],
            model=request.model,
            tokens_used=len(response["message"]["content"].split()) + len(request.prompt.split()),
            latency_ms=latency_ms
        )