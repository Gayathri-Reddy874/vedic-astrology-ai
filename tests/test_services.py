import pytest

from vedic_astro.services.ai_assistant import (
    FALLBACK_REPLY,
    PREDEFINED_QUESTIONS,
    VedicAIAssistant,
    build_chart_context,
    get_question_suggestions,
)
from vedic_astro.services.store import MemoryStore

from .conftest import FakeClient


def test_memory_store_ttl_and_eviction():
    now = [0.0]
    store = MemoryStore(max_entries=2, clock=lambda: now[0])
    store.set("a", 1, ttl=10)
    store.set("b", 2, ttl=10)
    store.set("c", 3, ttl=10)  # evicts the oldest ("a")
    assert store.get("a") is None and store.get("c") == 3
    now[0] = 11
    assert store.get("b") is None
    store.set("d", 4, ttl=5)
    store.delete("d")
    assert store.get("d") is None


def make(client=None, **kw):
    return VedicAIAssistant(store=MemoryStore(), client=client or FakeClient(), **kw)


def test_history_is_trimmed_to_window_and_stored():
    client = FakeClient()
    ai = make(client, history_window=2)
    for i in range(4):
        assert ai.get_response("u1", f"question {i}")["success"]
    sent = client.chat.completions.calls[-1]["messages"]
    # system + 2 history + current user message
    assert [m["role"] for m in sent] == ["system", "user", "assistant", "user"]
    assert sent[-1]["content"] == "question 3"


def test_clear_conversation_resets_history():
    client = FakeClient()
    ai = make(client)
    ai.get_response("u1", "hello")
    ai.clear_conversation("u1")
    ai.get_response("u1", "again")
    assert len(client.chat.completions.calls[-1]["messages"]) == 2


def test_long_messages_are_truncated():
    client = FakeClient()
    ai = make(client, max_message_chars=10)
    ai.get_response("u1", "x" * 500)
    assert client.chat.completions.calls[0]["messages"][-1]["content"] == "x" * 10


def test_provider_errors_are_hidden_from_client():
    ai = make(FakeClient(error=RuntimeError("sk-secret leaked")))
    result = ai.get_response("u1", "hello")
    assert result == {"success": False, "error": "ai_unavailable", "response": FALLBACK_REPLY}
    assert "sk-secret" not in str(result)


def test_requires_key_or_client():
    with pytest.raises(ValueError):
        VedicAIAssistant(store=MemoryStore())


def test_context_and_suggestions_use_chart_data():
    chart = {
        "Ascendant": {"sign": "Mesha", "sign_en": "Aries"},
        "Planets": {
            "Moon": {"sign": "Karka", "nakshatra": "Pushya", "degree": 3},
            "Saturn": {"sign": "Tula", "nakshatra": "Swati", "degree": 1},
        },
    }
    predictions = {
        "personality": {"lagna_nature": "dynamic"},
        "career": {"strength": "moderate"},
        "relationships": {"focus": "delayed but stable"},
        "life_purpose": "x",
        "challenges": {"manglik": True},
        "strengths": ["a", "b", "c", "d"],
    }
    ctx = build_chart_context(chart, predictions)
    assert "Mesha" in ctx and "Pushya" in ctx and "- Strength: d" not in ctx
    suggestions = get_question_suggestions(chart, predictions)
    assert "What are the effects of my Manglik dosha?" in suggestions
    assert len(suggestions) <= 8 and len(set(suggestions)) == len(suggestions)
    assert get_question_suggestions() == PREDEFINED_QUESTIONS


def test_redis_store_roundtrip(monkeypatch):
    import redis

    from vedic_astro.services.store import RedisStore, build_store

    class FakeRedis:
        data: dict = {}

        @classmethod
        def from_url(cls, url, decode_responses):
            assert decode_responses
            return cls()

        def get(self, key):
            return self.data.get(key)

        def set(self, key, value, ex):
            self.data[key] = value
            assert ex == 30

        def delete(self, key):
            self.data.pop(key, None)

    monkeypatch.setattr(redis, "Redis", FakeRedis)
    store = build_store("redis://example")
    assert isinstance(store, RedisStore)
    store.set("k", {"a": [1, 2]}, ttl=30)
    assert store.get("k") == {"a": [1, 2]} and FakeRedis.data == {"vedic:k": '{"a": [1, 2]}'}
    store.delete("k")
    assert store.get("k") is None
