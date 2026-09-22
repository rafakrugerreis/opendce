"""
Configuração de logging estruturado com mascaramento de dados sensíveis.
"""

from __future__ import annotations

import logging
import re
import sys

_SENSITIVE_PATTERNS = [
    (re.compile(r"(password|senha|cert_password|dce_cert_password)\s*=\s*\S+", re.I), r"\1=***"),
    (re.compile(r"(PRIVATE KEY-----)(.*?)(-----END)", re.S), r"\1[REDACTED]\3"),
]


class SensitiveDataFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = _mask(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: (_mask(v) if isinstance(v, str) else v) for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple((_mask(a) if isinstance(a, str) else a) for a in record.args)
        return True


def _mask(text: str) -> str:
    for pattern, replacement in _SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(SensitiveDataFilter())
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()
    root.addHandler(handler)


get_logger = logging.getLogger
