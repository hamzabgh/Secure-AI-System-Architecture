import re
from typing import Dict, List, Tuple
from fastapi import HTTPException, status

class LLMFirewall:
    """
    Infrastructure-level LLM Firewall
    Blocks attacks BEFORE they reach the model
    """
    
    # Prompt injection patterns
    INJECTION_PATTERNS = [
        r"(?i)ignore.*previous.*instructions",
        r"(?i)you.*are.*now.*a.*different.*ai",
        r"(?i)system.*prompt.*override",
        r"(?i)disregard.*all.*rules",
        r"(?i)admin.*access.*granted",
        r"(?i)###.*system.*:",
        r"(?i)<script.*?>.*?</script>",
        r"(?i)drop.*table",
        r"(?i)union.*select",
    ]
    
    # PII detection patterns
    PII_PATTERNS = {
        "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
    }
    
    # Toxicity keywords
    TOXIC_KEYWORDS = ["violence", "hate", "harassment", "illegal", "harm"]
    
    def __init__(self):
        self.compiled_patterns = [re.compile(p) for p in self.INJECTION_PATTERNS]
        self.compiled_pii = {k: re.compile(v) for k, v in self.PII_PATTERNS.items()}
    
    def scan_prompt(self, prompt: str, user_id: str) -> Tuple[bool, List[str]]:
        """
        Multi-layer prompt analysis
        Returns: (is_safe, violations)
        """
        violations = []
        
        # Layer 1: Prompt Injection Detection
        for pattern in self.compiled_patterns:
            if pattern.search(prompt):
                violations.append(f"Injection pattern detected: {pattern.pattern}")
        
        # Layer 2: PII Detection (block unless explicitly allowed)
        for pii_type, pattern in self.compiled_pii.items():
            if pattern.search(prompt):
                violations.append(f"PII detected: {pii_type}")
        
        # Layer 3: Token abuse detection (unusual token density)
        token_density = len(prompt.split()) / len(prompt)
        if token_density > 0.5:  # Too many short words
            violations.append("Potential token abuse: high token density")
        
        # Layer 4: Toxicity check
        prompt_lower = prompt.lower()
        if any(word in prompt_lower for word in self.TOXIC_KEYWORDS):
            violations.append("Toxic content detected")
        
        # Log violations
        if violations:
            from ..audit.logger import audit_log
            audit_log.log_security_event(
                "firewall_block",
                "high",
                {
                    "user_id": user_id,
                    "violations": violations,
                    "prompt_preview": prompt[:100]
                }
            )
        
        return len(violations) == 0, violations
    
    def enforce(self, prompt: str, user_id: str):
        """Blocking enforcement"""
        is_safe, violations = self.scan_prompt(prompt, user_id)
        if not is_safe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Request blocked by LLM Firewall",
                    "violations": violations
                }
            )

firewall = LLMFirewall()