"""PII redactor for logs and Sentry."""
import re
from typing import Any

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}\d")
SENSITIVE_KEYS = {"email", "phone", "password", "token", "api_key", "ssn"}


class PIIRedactor:
    def redact(self, value: Any) -> Any:
        if isinstance(value, str):
            return self._redact_string(value)
        if isinstance(value, dict):
            return {k: ("[REDACTED]" if k.lower() in SENSITIVE_KEYS else self.redact(v))
                    for k, v in value.items()}
        if isinstance(value, list):
            return [self.redact(v) for v in value]
        return value

    def _redact_string(self, s: str) -> str:
        s = EMAIL_RE.sub("[REDACTED_EMAIL]", s)
        s = PHONE_RE.sub("[REDACTED_PHONE]", s)
        return s
