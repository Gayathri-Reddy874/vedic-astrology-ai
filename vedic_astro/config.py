"""Environment-driven configuration."""

from __future__ import annotations

import logging
import os
import secrets
from dataclasses import dataclass

logger = logging.getLogger(__name__)


def _bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    env: str
    secret_key: str
    openai_api_key: str | None
    openai_model: str
    redis_url: str | None
    log_level: str
    trust_proxy: bool
    chat_rate_limit: str
    session_lifetime: int
    cookie_secure: bool

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @classmethod
    def from_env(cls) -> Settings:
        env = os.environ.get("APP_ENV", "development").lower()
        secret = os.environ.get("SECRET_KEY", "")
        if not secret:
            if env == "production":
                raise RuntimeError("SECRET_KEY must be set when APP_ENV=production.")
            secret = secrets.token_hex(32)
            logger.warning("SECRET_KEY not set; using an ephemeral key (sessions reset on restart)")
        return cls(
            env=env,
            secret_key=secret,
            openai_api_key=os.environ.get("OPENAI_API_KEY") or None,
            openai_model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            redis_url=os.environ.get("REDIS_URL") or None,
            log_level=os.environ.get("LOG_LEVEL", "INFO").upper(),
            trust_proxy=_bool("TRUST_PROXY"),
            chat_rate_limit=os.environ.get("CHAT_RATE_LIMIT", "20 per minute"),
            session_lifetime=int(os.environ.get("SESSION_LIFETIME", "3600")),
            cookie_secure=_bool("COOKIE_SECURE", default=env == "production"),
        )
