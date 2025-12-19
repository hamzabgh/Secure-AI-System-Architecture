from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from .service import auth_service
from app.core.security import security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


router = APIRouter(prefix="/auth", tags=["authentication"])

class LoginRequest(BaseModel):
    username: str
    password: str
    

class ScopedTokenRequest(BaseModel):
    model: str
    max_tokens: int
    scopes: list[str] = ["llm:generate"] 

@router.post("/login", response_model=dict)
async def login(credentials: LoginRequest):
    """Login with Argon2-secured credentials"""
    token = auth_service.authenticate(
        credentials.username, 
        credentials.password
    )
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    return {"access_token": token, "token_type": "bearer"}

security_scheme = HTTPBearer()   

@router.post("/scoped-token", response_model=dict)
async def get_scoped_token(
    body: ScopedTokenRequest,
    creds: HTTPAuthorizationCredentials = Depends(security_scheme)  
):
    user_token = creds.credentials   
    llm_token = auth_service.get_llm_scoped_token(
        user_token,
        body.model,
        body.max_tokens,
        body.scopes          # <-- here
    )
    return {"llm_token": llm_token, "expires_in": 60}