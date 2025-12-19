import time
import asyncio
from typing import Optional
from fastapi import HTTPException, status
from ..core.security import security
from ..core.rate_limit import rate_limiter
from ..core.zero_trust import zero_trust
from ..audit.logger import audit_log
from .schemas import LLMRequest, LLMResponse
from .adapters.openai import OpenAIAdapter
from .adapters.local import OllamaAdapter
from .firewall import firewall
from ..core.config import settings


class LLMOrchestrator:
    """
    Security brain for LLM routing
    Single choke point for all LLM requests
    """
    
    def __init__(self):
        self.adapters = {
            "gpt-4": OpenAIAdapter(),
            "gpt-3.5-turbo": OpenAIAdapter(),
            "llama2": OllamaAdapter(),
            "mistral": OllamaAdapter(),
            "phi":    OllamaAdapter(),
        }
    
    async def process_request(
        self, 
        request: LLMRequest, 
        llm_scoped_token: str
    ) -> LLMResponse:
        """
        Main security orchestration pipeline
        """
        start_time = time.time()
        
        # Step 1: Decode token
        token_data = security.decode_token(llm_scoped_token)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid LLM token"
            )
        
        user_id = token_data["sub"]
        
        # Step 2: Zero Trust verification
        zero_trust.verify_request(
            token_data,
            "llm",
            "generate",
            tokens=request.max_tokens,
            # rate_limit=lambda: rate_limiter.check_limits(
            #     user_id, "requests", 30, 60
            # )
            rate_limit=lambda: True
        )
        
        # Step 3: Rate limit token consumption
        if not rate_limiter.consume_tokens(user_id, request.max_tokens):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Token quota exceeded"
            )
        
        # Step 4: LLM Firewall inspection
        firewall.enforce(request.prompt, user_id)
        
        # Step 5: Route to adapter
        adapter = self.adapters.get(request.model)
        if not adapter:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported model"
            )
        
        # Step 6: Execute inference with timeout
        try:
            response = await asyncio.wait_for(
                adapter.generate(request),
                timeout=settings.inference_timeout_seconds
            )
        except asyncio.TimeoutError:
            audit_log.log_security_event(
                "inference_timeout",
                "medium",
                {"user_id": user_id, "model": request.model}
            )
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Inference timeout"
            )
        
        # Step 7: Audit logging
        latency_ms = (time.time() - start_time) * 1000
        audit_log.log_inference(
            user_id=user_id,
            model=request.model,
            prompt_tokens=len(request.prompt.split()),
            completion_tokens=len(response.content.split()),
            latency_ms=latency_ms,
            cost_usd=self._estimate_cost(request.model, request.max_tokens)
        )
        
        return response
    
    def _estimate_cost(self, model: str, tokens: int) -> float:
        """Cost estimation for budget tracking"""
        cost_per_1k = {
            "gpt-4": 0.03,
            "gpt-3.5-turbo": 0.0015,
            "llama2": 0.0,
            "mistral": 0.0,
            "phi": 0.0
        }
        return (tokens / 1000) * cost_per_1k.get(model, 0.0)

orchestrator = LLMOrchestrator()