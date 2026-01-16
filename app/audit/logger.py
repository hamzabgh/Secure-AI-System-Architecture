# app/audit/logger.py
import json
import logging
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logs."""
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        # merge any extra fields added via `extra=`
        if hasattr(record, "user_id"):
            log_obj.update(record.__dict__)
        return json.dumps(log_obj)


class AuditLogger:
    def __init__(self):
        self.logger = logging.getLogger("audit")
        if not self.logger.handlers:         
            handler = logging.StreamHandler()
            handler.setFormatter(JSONFormatter())
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    # ---------- convenience wrappers ----------
    def log_inference(self, user_id: str, model: str, prompt_tokens: int,
                      completion_tokens: int, latency_ms: float, cost_usd: float):
        self.logger.info("llm_inference", extra={
            "user_id": user_id,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "latency_ms": latency_ms,
            "cost_usd": cost_usd,
        })

    def log_security_event(self, event_type: str, severity: str, details: dict):
        self.logger.warning("security_event", extra={
            "event_type": event_type,
            "severity": severity,
            "details": details,
        })


audit_log = AuditLogger()