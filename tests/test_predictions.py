from vedic_astro.core.ephemeris import build_chart
from vedic_astro.core.models import BirthData
from vedic_astro.core.predictions import generate_prediction_signals, get_remedies, planet_houses

from .conftest import BIRTH


def test_signals_have_expected_shape():
    chart = build_chart(BirthData.from_mapping(BIRTH))
    signals = generate_prediction_signals(chart)
    for key in (
        "core_identity",
        "personality",
        "career",
        "relationships",
        "spiritual",
        "health",
        "challenges",
        "strengths",
        "life_purpose",
    ):
        assert key in signals
    assert signals["core_identity"]["ascendant"] == chart["Ascendant"]["sign"]
    assert signals["career"]["strength"] in {"moderate", "high"}


def test_planet_houses_are_in_range_and_use_lagna():
    chart = build_chart(BirthData.from_mapping(BIRTH))
    houses = planet_houses(chart)
    assert set(houses) == set(chart["Planets"])
    assert all(1 <= h <= 12 for h in houses.values())
    # Rahu and Ketu are always in opposite houses.
    assert (houses["Rahu"] - houses["Ketu"]) % 12 == 6


def test_remedies_follow_signals():
    base = {
        "challenges": {"manglik": True, "codes": ["saturn", "saturn", "rahu"]},
        "health": {"focus_areas": ["Heart/Circulation", "Mind/Emotions"]},
    }
    types = [r["type"] for r in get_remedies(base)]
    assert types == ["Manglik Dosha", "Saturn", "Rahu", "Heart Health", "Mental Peace"]


def test_general_remedy_when_nothing_detected():
    signals = {
        "challenges": {"manglik": False, "codes": []},
        "health": {"focus_areas": ["General wellness"]},
    }
    assert get_remedies(signals) == [
        {"type": "General", "remedy": "Regular worship, charity, and positive thinking"}
    ]


def synthetic_chart(**houses):
    """Chart with Mesha lagna where each planet sits in the requested house."""
    defaults = {
        "Sun": 3,
        "Moon": 3,
        "Mars": 3,
        "Mercury": 2,
        "Jupiter": 3,
        "Venus": 3,
        "Saturn": 3,
        "Rahu": 2,
        "Ketu": 8,
    }
    defaults.update(houses)
    planets = {
        name: {"longitude": 30 * (house - 1) + 5, "sign": "x", "nakshatra": "y"}
        for name, house in defaults.items()
    }
    planets["Moon"]["sign"] = "Karka"
    return {
        "Ascendant": {"longitude": 1.0, "sign": "Mesha", "sign_en": "Aries"},
        "Planets": planets,
    }


def test_rules_fire_for_strong_placements():
    chart = synthetic_chart(
        Sun=10, Mercury=6, Jupiter=9, Venus=7, Moon=4, Mars=3, Saturn=10, Ketu=12
    )
    s = generate_prediction_signals(chart)
    assert s["career"]["strength"] == "high" and s["career"]["leadership"]
    assert s["career"]["communication"] and s["relationships"]["focus"] == "high"
    assert s["spiritual"]["growth"] and s["spiritual"]["past_life"]
    assert s["career"]["suggested_fields"] == [
        "Public relations/Counseling",
        "Engineering/Military/Sports",
        "Writing/Teaching/Business",
    ]
    assert s["life_purpose"] == "Nurturing and connecting with others"


def test_challenge_rules_and_remedies():
    chart = synthetic_chart(Saturn=7, Mars=8, Rahu=8, Ketu=2, Sun=6, Moon=8)
    s = generate_prediction_signals(chart)
    assert s["relationships"]["delayed_marriage"]
    assert s["relationships"]["focus"] == "delayed but stable"
    assert s["challenges"]["manglik"] and s["challenges"]["manglik_house"] == 8
    assert s["challenges"]["codes"] == ["rahu", "mars"]
    focus = set(s["health"]["focus_areas"])
    assert {"Heart/Circulation", "Mind/Emotions", "Blood/Energy"} <= focus
    types = [r["type"] for r in get_remedies(s)]
    assert types[0] == "Manglik Dosha" and "Rahu" in types and "Mars" in types


def test_saturn_in_first_and_eighth_houses():
    assert (
        "Self-discipline and responsibility"
        in generate_prediction_signals(synthetic_chart(Saturn=1))["challenges"]["areas"]
    )
    assert (
        "Transformational challenges"
        in generate_prediction_signals(synthetic_chart(Saturn=8))["challenges"]["areas"]
    )


def test_ketu_eighth_and_multiple_marriage_flags():
    s = generate_prediction_signals(synthetic_chart(Ketu=8, Jupiter=7, Venus=2, Rahu=11))
    assert "Letting go of attachments" in s["challenges"]["areas"]
    assert s["relationships"]["multiple_marriages"] == "possible"
    assert s["relationships"]["early_marriage"]
    assert s["life_purpose"] == "Material success and innovation"
