import pytest

from .conftest import BIRTH


@pytest.fixture
def captured(monkeypatch):
    """Replace template rendering so tests don't depend on the HTML files."""
    seen = {}

    def fake_render(template, **ctx):
        seen["template"], seen["ctx"] = template, ctx
        return f"rendered:{template}"

    monkeypatch.setattr("vedic_astro.web.pages.render_template", fake_render)
    return seen


def test_health(client):
    body = client.get("/health").get_json()
    assert body["status"] == "ok"


def test_security_headers_and_request_id(client):
    r = client.get("/health", headers={"X-Request-ID": "abc123"})
    assert r.headers["X-Request-ID"] == "abc123"
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"


def test_horoscope_api_success_and_shape(client):
    body = client.post("/api/horoscope", json=BIRTH).get_json()
    assert body["success"]
    assert set(body["data"]) == {"Ascendant", "Planets", "Houses", "Panchanga", "JulianDay"}
    assert len(body["data"]["Planets"]) == 9


@pytest.mark.parametrize("payload", [None, [], {"year": 2000}, BIRTH | {"latitude": 123}])
def test_horoscope_api_rejects_bad_input(client, payload):
    r = client.post("/api/horoscope", json=payload)
    assert r.status_code == 400
    assert r.get_json()["success"] is False


def test_unknown_api_route_returns_json_404(client):
    r = client.get("/api/nope")
    assert r.status_code == 404 and r.get_json()["error"] == "Not found"


def test_chart_page_stores_context_and_enables_chat(client, captured):
    r = client.post("/chart", data={k: str(v) for k, v in BIRTH.items()} | {"name": "Asha"})
    assert r.status_code == 200
    ctx = captured["ctx"]
    assert captured["template"] == "chart.html" and ctx["name"] == "Asha"
    assert ctx["birth_details"]["date"] == "01/01/2000"
    assert ctx["chart"]["Ascendant"]["sign"] == "Kumbha"

    reply = client.post("/api/chat", json={"message": "What is my life purpose?"})
    assert reply.status_code == 200 and reply.get_json()["success"]
    assert client.get("/api/chat/suggestions").get_json()["suggestions"]
    assert client.post("/api/chat/clear").get_json()["success"]


def test_chat_prompt_contains_chart_after_chart_page(client, captured, fake_client):
    client.post("/chart", data={k: str(v) for k, v in BIRTH.items()})
    client.post("/api/chat", json={"message": "hi"})
    system_prompt = fake_client.chat.completions.calls[-1]["messages"][0]["content"]
    assert "ASTROLOGICAL CONTEXT" in system_prompt and "Kumbha" in system_prompt


def test_match_page_defaults_time_and_scores(client, captured):
    form = {
        "boy_year": 1995,
        "boy_month": 5,
        "boy_day": 10,
        "boy_name": "Ravi",
        "girl_year": 1997,
        "girl_month": 8,
        "girl_day": 20,
        "latitude": 12.97,
        "longitude": 77.59,
    }
    assert client.post("/match", data=form).status_code == 200
    assert captured["template"] == "match_result.html"
    assert captured["ctx"]["boy_name"] == "Ravi" and captured["ctx"]["girl_name"] == "Girl"
    assert 0 <= captured["ctx"]["match"]["total"] <= 36


def test_match_page_validation_error_rerenders_form(client, monkeypatch):
    seen = {}
    monkeypatch.setattr(
        "vedic_astro.render_template",
        lambda template, **ctx: seen.update(template=template, ctx=ctx) or "x",
    )
    r = client.post("/match", data={"boy_year": 1995})
    assert r.status_code == 400 and seen["template"] == "compatibility.html"
    assert "required" in seen["ctx"]["error"]


def test_predictions_redirects_without_chart(client):
    assert client.get("/predictions").status_code == 302
    assert client.get("/predictions/legacy-token").status_code == 302


@pytest.mark.parametrize("payload", [None, {}, {"message": "   "}, {"message": 5}])
def test_chat_rejects_empty_messages(client, payload):
    assert client.post("/api/chat", json=payload).status_code == 400


def test_chat_unavailable_without_api_key(app_no_ai):
    r = app_no_ai.test_client().post("/api/chat", json={"message": "hi"})
    assert r.status_code == 503 and r.get_json()["error"] == "ai_unavailable"


def test_chat_is_rate_limited(app):
    app.config["CHAT_RATE_LIMIT"] = "2 per minute"
    c = app.test_client()
    codes = [c.post("/api/chat", json={"message": "hi"}).status_code for _ in range(3)]
    assert codes == [200, 200, 429]


def test_production_requires_secret_key(monkeypatch):
    from vedic_astro import create_app

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app()


def test_unexpected_errors_are_hidden(client, monkeypatch):
    def boom(_birth):
        raise RuntimeError("database password is hunter2")

    monkeypatch.setattr("vedic_astro.web.api.build_chart", boom)
    client.application.config["PROPAGATE_EXCEPTIONS"] = False
    r = client.post("/api/horoscope", json=BIRTH)
    assert r.status_code == 500
    assert "hunter2" not in r.get_data(as_text=True)


def test_simple_pages_render_expected_templates(client, captured):
    for path, template in (
        ("/", "index.html"),
        ("/about", "about.html"),
        ("/compatibility", "compatibility.html"),
        ("/ai-chat", "ai_chat.html"),
    ):
        assert client.get(path).status_code == 200
        assert captured["template"] == template
    assert captured["ctx"]["suggestions"]


def test_predictions_page_after_chart(client, captured):
    client.post("/chart", data={k: str(v) for k, v in BIRTH.items()})
    assert client.get("/predictions").status_code == 200
    assert captured["template"] == "predictions.html"


def test_cookie_secure_follows_environment(monkeypatch):
    from vedic_astro import create_app

    monkeypatch.setenv("SECRET_KEY", "s")
    monkeypatch.setenv("APP_ENV", "production")
    assert create_app().config["SESSION_COOKIE_SECURE"] is True
    monkeypatch.setenv("COOKIE_SECURE", "0")
    assert create_app().config["SESSION_COOKIE_SECURE"] is False


LEGACY_ENDPOINTS = [
    "index",
    "about",
    "compatibility",
    "chart",
    "match_kundalis",
    "ai_chat",
    "show_predictions",
    "chat_with_ai",
    "clear_chat",
    "get_suggestions",
    "api_horoscope",
]


def test_original_endpoint_names_still_exist(app):
    """Existing templates call url_for('index'), url_for('chart'), ... without a prefix."""
    assert set(LEGACY_ENDPOINTS) <= set(app.view_functions)
    with app.test_request_context():
        from flask import url_for

        assert url_for("index") == "/"
        assert url_for("chart") == "/chart"
        assert url_for("match_kundalis") == "/match"
        assert url_for("ai_chat") == "/ai-chat"
        assert url_for("static", filename="css/x.css") == "/static/css/x.css"


def test_template_with_url_for_renders(app):
    from flask import render_template_string

    html = "{{ url_for('index') }} {{ url_for('about') }} {{ url_for('compatibility') }}"
    with app.test_request_context():
        assert render_template_string(html) == "/ /about /compatibility"
