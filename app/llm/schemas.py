from pydantic import BaseModel, Field, validator
from typing import Literal, Optional, List
from ..core.config import settings

class LLMRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10000)
    model: Literal["gpt-4", "gpt-3.5-turbo", "llama2", "mistral", "phi"] = "gpt-4"
    max_tokens: int = Field(512, ge=1, le=2048)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    
    @validator("max_tokens")
    def validate_max_tokens(cls, v, values):
        if v > settings.max_tokens_per_request:
            raise ValueError(f"Max tokens exceeded: {v}")
        return v

class LLMResponse(BaseModel):
    content: str
    model: str
    tokens_used: int
    latency_ms: float

class ScopedTokenRequest(BaseModel):
    model: str
    max_tokens: int
    scope: List[str]