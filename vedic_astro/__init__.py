"""Vedic Astrology AI - application factory."""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime
from typing import Any

from flask import Flask, g, jsonify, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Settings
from .core.errors import ValidationError
from .extensions import limiter
from .services.ai_assistant import VedicAIAssistant
from .services.store import build_store

__version__ = "1.0.0"
logger = logging.getLogger(__name__)


def create_app(overrides: dict[str, Any] | None = None) -> Flask:
    try:  # optional: load .env during local development
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:  # pragma: no cover
        pass

    settings = Settings.from_env()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.update(
        SECRET_KEY=settings.secret_key,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=settings.cookie_secure,
        PERMANENT_SESSION_LIFETIME=settings.session_lifetime,
        MAX_CONTENT_LENGTH=64 * 1024,
        RATELIMIT_STORAGE_URI=settings.redis_url or "memory://",
        CHAT_RATE_LIMIT=settings.chat_rate_limit,
        SETTINGS=settings,
    )
    if overrides:
        app.config.update(overrides)
    if settings.trust_proxy:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)  # type: ignore[method-assign]

    limiter.init_app(app)

    store = build_store(settings.redis_url)
    app.extensions["store"] = store
    app.extensions["ai_assistant"] = _build_assistant(app, settings, store)

    from .web import api, pages

    pages.register(app)
    api.register(app)
    _register_hooks(app)
    _register_error_handlers(app)
    return app


def _build_assistant(app: Flask, settings: Settings, store) -> VedicAIAssistant | None:
    injected = app.config.get("AI_CLIENT")
    if injected is None and not settings.openai_api_key:
        logger.warning("OPENAI_API_KEY not set; AI chat is disabled.")
        return None
    return VedicAIAssistant(
        store=store,
        api_key=settings.openai_api_key,
        client=injected,
        model=settings.openai_model,
    )


def _register_hooks(app: Flask) -> None:
    @app.context_processor
    def inject_globals() -> dict[str, Any]:
        return {"current_year": datetime.now().year, "app_version": __version__}

    @app.before_request
    def start_timer() -> None:
        g.started = time.perf_counter()
        g.request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]

    @app.after_request
    def finish(response):
        response.headers["X-Request-ID"] = g.get("request_id", "-")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        if request.path != "/health":
            elapsed = (time.perf_counter() - g.get("started", time.perf_counter())) * 1000
            logger.info(
                "%s %s -> %s (%.0f ms) rid=%s",
                request.method,
                request.path,
                response.status_code,
                elapsed,
                g.get("request_id"),
            )
        return response


def _register_error_handlers(app: Flask) -> None:
    def wants_json() -> bool:
        return request.path.startswith("/api/")

    @app.errorhandler(ValidationError)
    def handle_validation(exc: ValidationError):
        if wants_json():
            return jsonify(success=False, error=str(exc)), 400
        template = "compatibility.html" if request.path == "/match" else "index.html"
        return render_template(template, error=str(exc)), 400

    @app.errorhandler(404)
    def handle_404(_exc):
        if wants_json():
            return jsonify(success=False, error="Not found"), 404
        return render_template("index.html", error="Page not found."), 404

    @app.errorhandler(429)
    def handle_429(_exc):
        return jsonify(
            success=False,
            error="rate_limited",
            response="You're asking too quickly. Please wait a moment and try again.",
        ), 429

    @app.errorhandler(Exception)
    def handle_unexpected(exc: Exception):
        from werkzeug.exceptions import HTTPException

        if isinstance(exc, HTTPException):
            return exc
        logger.exception("Unhandled error rid=%s", g.get("request_id"))
        if wants_json():
            return jsonify(success=False, error="Internal server error"), 500
        return render_template("index.html", error="Something went wrong. Please try again."), 500
