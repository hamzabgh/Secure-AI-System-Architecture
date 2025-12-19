import argon2
from datetime import datetime, timedelta
from jose import jwt, JWTError
from typing import Optional
from ..core.config import settings

class SecurityManager:
    def __init__(self):
        self.ph = argon2.PasswordHasher(
            time_cost=settings.argon2_time_cost,
            memory_cost=settings.argon2_memory_cost,
            parallelism=settings.argon2_parallelism,
            hash_len=32,
            salt_len=16,
            encoding='utf-8',
            type=argon2.Type.ID
        )
    
    def hash_password(self, password: str) -> str:
        """Hash password with Argon2 (GPU-resistant)"""
        return self.ph.hash(password)
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify Argon2 hash with timing-attack resistance"""
        try:
            self.ph.verify(hashed, password)
            if self.ph.check_needs_rehash(hashed):
                # Log for async rehashing
                pass
            return True
        except argon2.exceptions.VerifyMismatchError:
            return False
    
    def create_user_token(self, user_id: str) -> str:
        """Create 15-min user identity token"""
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
        payload = {
            "sub": user_id,
            "type": "user",
            "exp": expire
        }
        return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    
    def create_llm_scoped_token(self, user_id: str, scope: list, model: str, 
                                max_tokens: int) -> str:
        """Create 60-sec scoped LLM token"""
        expire = datetime.utcnow() + timedelta(
            seconds=settings.llm_token_expire_seconds
        )
        payload = {
            "sub": user_id,
            "type": "llm",
            "scope": scope,
            "model": model,
            "max_tokens": max_tokens,
            "exp": expire
        }
        return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    
    def decode_token(self, token: str) -> Optional[dict]:
        """Decode and validate JWT token"""
        try:
            return jwt.decode(token, settings.secret_key, 
                            algorithms=[settings.algorithm])
        except JWTError:
            return None

security = SecurityManager()