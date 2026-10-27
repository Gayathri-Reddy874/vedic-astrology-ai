"""Per-visitor server-side state keyed by an opaque session id."""

from __future__ import annotations

import uuid
from typing import Any

from flask import current_app, session

CONTEXT_TTL = 3600


def session_id() -> str:
    """Return (creating if needed) the visitor's opaque id; only this lives in the cookie."""
    if "sid" not in session:
        session["sid"] = uuid.uuid4().hex
    session.permanent = True
    return session["sid"]


def save_context(chart: dict[str, Any], predictions: dict[str, Any], remedies: list) -> None:
    current_app.extensions["store"].set(
        f"chart:{session_id()}",
        {"chart": chart, "predictions": predictions, "remedies": remedies},
        CONTEXT_TTL,
    )


def load_context() -> dict[str, Any] | None:
    return current_app.extensions["store"].get(f"chart:{session_id()}")
