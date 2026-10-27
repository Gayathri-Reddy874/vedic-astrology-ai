"""HTML pages. Template names and context keys match the original templates."""

from __future__ import annotations

from collections.abc import Callable

from flask import Flask, redirect, render_template, request, url_for

from ..core.ephemeris import build_chart
from ..core.matching import match_kundalis as score_match
from ..core.models import BirthData
from ..core.predictions import generate_prediction_signals, get_remedies
from ..services.ai_assistant import get_question_suggestions
from .helpers import load_context, save_context, session_id

_ROUTES: list[tuple[str, tuple[str, ...], Callable]] = []


def route(rule: str, methods: tuple[str, ...] = ("GET",)):
    """Collect a view; the endpoint name is the function name (matches the old app)."""

    def decorator(func: Callable) -> Callable:
        _ROUTES.append((rule, methods, func))
        return func

    return decorator


def register(app: Flask) -> None:
    for rule, methods, func in _ROUTES:
        app.add_url_rule(rule, endpoint=func.__name__, view_func=func, methods=list(methods))


@route("/")
def index():
    return render_template("index.html", title="Vedic Astrology - Cosmic Green")


@route("/about")
def about():
    return render_template("about.html", title="About - Vedic Astrology")


@route("/compatibility")
def compatibility():
    return render_template("compatibility.html", title="Kundali Matching - Cosmic Green")


@route("/chart", ("POST",))
def chart():
    birth = BirthData.from_mapping(request.form)
    chart_data = build_chart(birth)
    predictions = generate_prediction_signals(chart_data)
    remedies = get_remedies(predictions)
    save_context(chart_data, predictions, remedies)
    return render_template(
        "chart.html",
        title=f"{birth.name}'s Chart - Cosmic Green" if birth.name else "Your Chart - Cosmic Green",
        name=birth.name,
        birth_details={
            "date": f"{birth.day:02d}/{birth.month:02d}/{birth.year}",
            "time": f"{birth.hour:02d}:{birth.minute:02d}:{birth.second:02d}",
            "timezone": f"GMT{birth.timezone:+.1f}",
            "latitude": birth.latitude,
            "longitude": birth.longitude,
        },
        chart=chart_data,
        predictions=predictions,
        remedies=remedies,
    )


@route("/match", ("POST",))
def match_kundalis():
    # Birth time is optional (defaults to noon) but improves Moon accuracy.
    boy = BirthData.from_mapping(request.form, prefix="boy_", default_hour=12)
    girl = BirthData.from_mapping(request.form, prefix="girl_", default_hour=12)
    return render_template(
        "match_result.html",
        title="Matching Results - Cosmic Green",
        boy_name=boy.name or "Boy",
        girl_name=girl.name or "Girl",
        match=score_match(boy, girl),
    )


@route("/predictions")
@route("/predictions/<path:chart_data>")
def show_predictions(chart_data: str | None = None):
    ctx = load_context()
    if not ctx:
        return redirect(url_for("index"))
    return render_template(
        "predictions.html",
        title="Personal Predictions - Cosmic Green",
        chart=ctx["chart"],
        predictions=ctx["predictions"],
        remedies=ctx["remedies"],
    )


@route("/ai-chat")
def ai_chat():
    session_id()
    ctx = load_context() or {}
    return render_template(
        "ai_chat.html",
        title="AI Astrologer - Cosmic Green",
        suggestions=get_question_suggestions(ctx.get("chart"), ctx.get("predictions")),
    )
