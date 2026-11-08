from dataclasses import dataclass
import re
from typing import Protocol


@dataclass(frozen=True)
class GuardrailCheckResult:
    is_safe: bool
    reason: str | None = None
    sanitized_text: str = ""


class Guardrail(Protocol):
    def check_input(self, text: str) -> GuardrailCheckResult: ...
    def sanitize_output(self, text: str) -> str: ...


class PIIRedactor:
    """Detects and scrubs common sensitive banking data (cards, SSNs, secrets)."""

    # 13 to 19 digit payment card numbers (with or without dashes/spaces)
    CARD_REGEX = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
    # US Social Security Number pattern (XXX-XX-XXXX)
    SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
    # Common password declarations in prompt
    PASSWORD_REGEX = re.compile(r"(password\s*[:=]\s*)(\S+)", re.IGNORECASE)

    @classmethod
    def redact(cls, text: str) -> str:
        # Redact payment card numbers (keep last 4 digits)
        def mask_card(match: re.Match) -> str:
            raw = re.sub(r"\D", "", match.group(0))
            if len(raw) >= 13:
                return f"****-****-****-{raw[-4:]}"
            return match.group(0)

        result = cls.CARD_REGEX.sub(mask_card, text)
        result = cls.SSN_REGEX.sub("***-**-****", result)
        result = cls.PASSWORD_REGEX.sub(r"\1[REDACTED]", result)
        return result


class RuleBasedGuardrail:
    """Local, deterministic input and output guardrail for security defense-in-depth."""

    INJECTION_PATTERNS = [
        re.compile(r"ignore\s+(previous|all)\s+(instructions|rules)", re.IGNORECASE),
        re.compile(r"system\s+override", re.IGNORECASE),
        re.compile(r"disregard\s+(the\s+)?(rules|guardrails|safety)", re.IGNORECASE),
        re.compile(r"reveal\s+(administrative|system|api|root)\s+keys?", re.IGNORECASE),
        re.compile(r"print\s+the\s+system\s+prompt", re.IGNORECASE),
        re.compile(r"you\s+are\s+now\s+in\s+developer\s+mode", re.IGNORECASE),
    ]

    SECURITY_REFUSAL_MESSAGE = (
        "I cannot fulfill this request. Security policies strictly prohibit "
        "bypassing guardrails, executing unauthorized actions, or accessing administrative data."
    )

    def check_input(self, text: str) -> GuardrailCheckResult:
        cleaned = text.strip()
        for pattern in self.INJECTION_PATTERNS:
            if pattern.search(cleaned):
                return GuardrailCheckResult(
                    is_safe=False,
                    reason="Prompt Injection or System Override detected",
                    sanitized_text=self.SECURITY_REFUSAL_MESSAGE,
                )

        return GuardrailCheckResult(
            is_safe=True,
            reason=None,
            sanitized_text=cleaned,
        )

    def sanitize_output(self, text: str) -> str:
        """Applies PII redaction before returning text to users or logs."""
        return PIIRedactor.redact(text)


class BedrockGuardrailsAdapter:
    """AWS Bedrock Guardrails service client.
    Can be configured with a guardrailIdentifier and guardrailVersion.
    """

    def __init__(
        self,
        guardrail_id: str = "mock-guardrail",
        guardrail_version: str = "DRAFT",
        region_name: str = "us-east-1",
    ):
        self.guardrail_id = guardrail_id
        self.guardrail_version = guardrail_version
        self.fallback = RuleBasedGuardrail()

    def check_input(self, text: str) -> GuardrailCheckResult:
        # In offline/mock mode, delegate to RuleBasedGuardrail
        return self.fallback.check_input(text)

    def sanitize_output(self, text: str) -> str:
        return self.fallback.sanitize_output(text)