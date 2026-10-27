"""JSON API."""

from __future__ import annotations

from collections.abc import Callable

from flask import Flask, current_app, jsonify, request

from .. import __version__
from ..core.ephemeris import build_chart
from ..core.errors import ValidationError
from ..core.models import BirthData
from ..extensions import limiter
from ..services.ai_assistant import get_question_suggestions
from .helpers import load_context, session_id

_ROUTES: list[tuple[str, tuple[str, ...], Callable]] = []


def route(rule: str, methods: tuple[str, ...] = ("GET",)):
    def decorator(func: Callable) -> Callable:
        _ROUTES.append((rule, methods, func))
        return func

    return decorator


def register(app: Flask) -> None:
    for rule, methods, func in _ROUTES:
        app.add_url_rule(rule, endpoint=func.__name__, view_func=func, methods=list(methods))


@route("/health")
def health():
    return jsonify(status="ok", version=__version__)


@route("/api/horoscope", ("POST",))
def api_horoscope():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationError("Request body must be a JSON object.")
    return jsonify(success=True, data=build_chart(BirthData.from_mapping(payload)))


@route("/api/chat", ("POST",))
@limiter.limit(lambda: current_app.config["CHAT_RATE_LIMIT"])
def chat_with_ai():
    assistant = current_app.extensions["ai_assistant"]
    if assistant is None:
        return jsonify(
            success=False,
            error="ai_unavailable",
            response="The AI service is currently unavailable. Please try again later.",
        ), 503
    payload = request.get_json(silent=True)
    message = payload.get("message") if isinstance(payload, dict) else None
    if not isinstance(message, str) or not message.strip():
        return jsonify(success=False, error="empty_message", response="Please ask a question."), 400
    ctx = load_context() or {}
    result = assistant.get_response(
        session_id(), message, chart=ctx.get("chart"), predictions=ctx.get("predictions")
    )
    return jsonify(result), (200 if result["success"] else 502)


@route("/api/chat/clear", ("POST",))
def clear_chat():
    assistant = current_app.extensions["ai_assistant"]
    if assistant is None:
        return jsonify(success=False, error="ai_unavailable"), 503
    return jsonify(assistant.clear_conversation(session_id()))


@route("/api/chat/suggestions")
def get_suggestions():
    ctx = load_context() or {}
    return jsonify(
        success=True,
        suggestions=get_question_suggestions(ctx.get("chart"), ctx.get("predictions")),
    )
