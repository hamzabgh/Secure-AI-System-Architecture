from fastapi import APIRouter, Depends, Header, HTTPException,status
from typing import Annotated
from app.llm.schemas import LLMRequest, LLMResponse
from app.llm.orchestrator import orchestrator
from app.core.security import security

router = APIRouter(prefix="/llm", tags=["llm"])

async def verify_llm_token(
    x_llm_token: Annotated[str, Header()]
) -> str:
    """Extract and validate LLM scoped token from header"""
    token_data = security.decode_token(x_llm_token)
    if not token_data or token_data.get("type") != "llm":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid LLM token"
        )
    return x_llm_token

@router.post("/generate", response_model=LLMResponse)
async def generate(
    request: LLMRequest,
    llm_token: str = Depends(verify_llm_token)
):
    """
    Generate LLM response via secured orchestrator
    Header required: X-LLM-Token (60s lifetime)
    """
    return await orchestrator.process_request(request, llm_token)