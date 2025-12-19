from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    app_name: str = "SecureAI"
    app_version: str = "1.0.0"
    api_v1_prefix: str = "/api/v1"

    debug: bool = False
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    llm_token_expire_seconds: int = 60
    
    # Argon2
    argon2_time_cost: int = 4
    argon2_memory_cost: int = 131072
    argon2_parallelism: int = 8
    
    # Rate Limiting
    redis_url: str = "redis://localhost:6379/0"
    
    # APIs
    openai_api_key: str
    ollama_base_url: str = "http://localhost:11434"
    
    # GPU Protection
    max_tokens_per_request: int = 512
    max_tokens_per_hour: int = 10000
    inference_timeout_seconds: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()