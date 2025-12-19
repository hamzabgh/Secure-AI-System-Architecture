import signal
import sys
import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from .core.config import settings
from .api.v1 import llm
from app.auth import router as auth_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_credentials=True,
        allow_methods=["POST"],
        allow_headers=["X-LLM-Token", "Authorization"],
    )

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1"],
    )

    app.include_router(auth_router.router)
    app.include_router(llm.router, prefix=settings.api_v1_prefix)

    return app


app = create_app()


# 🔹 Proper Ctrl+C handling
def shutdown_handler(sig, frame):
    print("\n🛑 Shutting down FastAPI gracefully...")
    sys.exit(0)


signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",   
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info",
    )
