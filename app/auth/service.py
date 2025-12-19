from typing import Optional
from fastapi import HTTPException, status
from app.core.security import security
from app.core.rate_limit import rate_limiter

class AuthService:
    """
    Authentication service with Argon2
    No long-lived tokens
    """
    
    def __init__(self):
        # In production, use actual user database
        self.users_db = {
            "admin": {
                "hashed_password": security.hash_password("secure_admin_pass"),
                "plan": "premium"
            }
        }
    
    def authenticate(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return user JWT"""
        user = self.users_db.get(username)
        if not user:
            # Timing attack protection - still hash dummy
            security.verify_password("dummy", security.hash_password("dummy"))
            return None
        
        if security.verify_password(password, user["hashed_password"]):
            return security.create_user_token(username)
        
        return None
    
    def get_llm_scoped_token(self, user_token: str, model: str, 
                            max_tokens: int,
                            scopes: list[str]) -> str:
        """Exchange user token for scoped LLM token"""
        token_data = security.decode_token(user_token)
        if not token_data or token_data.get("type") != "user":
            raise HTTPException(401, "Invalid user token")

        return security.create_llm_scoped_token(
            user_id=token_data["sub"],
            scope=scopes,              
            model=model,
            max_tokens=max_tokens
        )
    
    def get_user_plan(self, user_id: str) -> str:
        """Get user plan for quota enforcement"""
        user = self.users_db.get(user_id, {})
        return user.get("plan", "free")

auth_service = AuthService()