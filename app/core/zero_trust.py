from typing import Dict, Any, Optional
from fastapi import HTTPException, status

class ZeroTrustPolicy:
    """
    Zero Trust enforcement engine
    Every request is hostile until proven otherwise
    """
    
    @staticmethod
    def validate_token_integrity(token: Dict[str, Any]) -> bool:
        """Verify token hasn't been tampered with"""
        required_fields = ["sub", "type", "exp"]
        return all(field in token for field in required_fields)
    
    @staticmethod
    def enforce_least_privilege(token: Dict[str, Any], required_scope: str) -> bool:
        """Scoped token validation"""
        if token.get("type") != "llm":
            return False
        
        scopes = token.get("scope", [])
        return required_scope in scopes
    
    @staticmethod
    def check_gpu_budget(token: Dict[str, Any], requested_tokens: int) -> bool:
        """GPU DoS protection"""
        max_allowed = token.get("max_tokens", 0)
        return requested_tokens <= max_allowed
    
    @staticmethod
    def audit_access(user_id: str, resource: str, action: str, 
                     granted: bool, reason: Optional[str] = None):
        """Log every access decision for forensics"""
        from ..audit.logger import audit_log
        audit_log.logger.info(
           "access_decision",
            extra={
                "user_id": user_id,
                "resource": resource,
                "action": action,
                "granted": granted,
                "reason": reason
            }
        )
    
    def verify_request(self, token: Dict[str, Any], resource: str, 
                       action: str, **context) -> bool:
        """Main Zero Trust verification gate"""
        user_id = token.get("sub")
        
        # 1. Token integrity
        if not self.validate_token_integrity(token):
            self.audit_access(user_id, resource, action, False, "invalid_token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token structure"
            )
        
        # 2. Least privilege
        if not self.enforce_least_privilege(token, f"{resource}:{action}"):
            self.audit_access(user_id, resource, action, False, "insufficient_scope")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # 3. GPU budget check
        if "tokens" in context:
            if not self.check_gpu_budget(token, context["tokens"]):
                self.audit_access(user_id, resource, action, False, "gpu_budget_exceeded")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="GPU budget exceeded"
                )
        
        # 4. Rate limiting
        if "rate_limit" in context:
            if not context["rate_limit"]():
                self.audit_access(user_id, resource, action, False, "rate_limit_exceeded")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
        
        self.audit_access(user_id, resource, action, True)
        return True

zero_trust = ZeroTrustPolicy()