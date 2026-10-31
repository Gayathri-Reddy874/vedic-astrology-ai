import pytest

from vedic_astro import create_app


class FakeCompletions:
    def __init__(self, reply="Namaste. Jupiter favours patience.", error=None):
        self.reply, self.error, self.calls = reply, error, []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error

        class _Msg:
            content = self.reply

        class _Choice:
            message = _Msg()

        class _Resp:
            choices = [_Choice()]

        return _Resp()


class FakeClient:
    def __init__(self, **kwargs):
        self.chat = type("Chat", (), {"completions": FakeCompletions(**kwargs)})()


@pytest.fixture
def fake_client():
    return FakeClient()


@pytest.fixture
def app(fake_client):
    return create_app({"TESTING": True, "AI_CLIENT": fake_client})


@pytest.fixture
def app_no_ai(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    return create_app({"TESTING": True})


@pytest.fixture
def client(app):
    return app.test_client()


BIRTH = {
    "year": 2000,
    "month": 1,
    "day": 1,
    "hour": 10,
    "minute": 30,
    "second": 0,
    "latitude": 12.9716,
    "longitude": 77.5946,
    "timezone": 5.5,
}

