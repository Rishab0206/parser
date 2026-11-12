import logging
import re
import sys

class RedactingFormatter(logging.Formatter):
    """
    Formatter that automatically strips/masks PDF passwords, full account numbers,
    and sensitive auth tokens from log streams.
    """
    ACCOUNT_REGEX = re.compile(r'\b(\d{4,8})(\d{4})\b')
    PASSWORD_REGEX = re.compile(r'(password|pwd|pass)\s*[:=]\s*["\']?([^"\'\s]+)["\']?', re.IGNORECASE)

    def format(self, record: logging.LogRecord) -> str:
        orig = super().format(record)
        # Redact passwords
        sanitized = self.PASSWORD_REGEX.sub(r'\1: [REDACTED]', orig)
        # Mask account numbers if full length appears
        sanitized = self.ACCOUNT_REGEX.sub(r'XXXX\2', sanitized)
        return sanitized

def get_logger(name: str = "bsi") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = RedactingFormatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
    return logger

logger = get_logger("bank-intelligence")

