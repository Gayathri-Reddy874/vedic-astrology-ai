"""Rule-based prediction signals and remedies derived from a computed chart."""

from __future__ import annotations

from typing import Any

from .constants import MANGLIK_HOUSES
from .ephemeris import house_of

_LAGNA_NATURE = {
    "Mesha": "dynamic and pioneering",
    "Vrishabha": "stable and sensual",
    "Mithuna": "communicative and adaptable",
    "Karka": "emotional and nurturing",
    "Simha": "confident and creative",
    "Kanya": "analytical and practical",
    "Tula": "diplomatic and balanced",
    "Vrischika": "intense and transformative",
    "Dhanu": "optimistic and philosophical",
    "Makara": "ambitious and disciplined",
    "Kumbha": "innovative and humanitarian",
    "Meena": "compassionate and intuitive",
}

_MOON_INFLUENCE = {
    "Mesha": "quick emotions",
    "Vrishabha": "stable emotions",
    "Mithuna": "changeable emotions",
    "Karka": "deep emotions",
    "Simha": "dramatic emotions",
    "Kanya": "analytical emotions",
    "Tula": "balanced emotions",
    "Vrischika": "intense emotions",
    "Dhanu": "optimistic emotions",
    "Makara": "cautious emotions",
    "Kumbha": "detached emotions",
    "Meena": "compassionate emotions",
}


def planet_houses(chart: dict[str, Any]) -> dict[str, int]:
    """Whole-sign house of every planet, counted from the Lagna."""
    asc = chart["Ascendant"]["longitude"]
    return {name: house_of(p["longitude"], asc) for name, p in chart["Planets"].items()}


def generate_prediction_signals(chart: dict[str, Any]) -> dict[str, Any]:
    planets = chart["Planets"]
    asc = chart["Ascendant"]
    h = planet_houses(chart)
    sun, moon, mars, mercury = h["Sun"], h["Moon"], h["Mars"], h["Mercury"]
    jupiter, venus, saturn = h["Jupiter"], h["Venus"], h["Saturn"]
    rahu, ketu = h["Rahu"], h["Ketu"]

    signals: dict[str, Any] = {
        "core_identity": {
            "ascendant": asc["sign"],
            "ascendant_en": asc["sign_en"],
            "moon_sign": planets["Moon"]["sign"],
            "moon_nakshatra": planets["Moon"]["nakshatra"],
        },
        "personality": {
            "lagna_nature": _LAGNA_NATURE.get(asc["sign"], "unique"),
            "emotional_nature": _MOON_INFLUENCE.get(planets["Moon"]["sign"], "balanced"),
        },
        "career": {"strength": "moderate"},
        "relationships": {"focus": "moderate"},
        "spiritual": {"growth": False},
        "health": {"focus_areas": []},
        "challenges": {"areas": []},
        "strengths": [],
    }
    strengths: list[str] = signals["strengths"]

    # Career
    career = signals["career"]
    if jupiter in (1, 2, 5, 9, 10, 11):
        career["strength"] = "high"
        strengths.append("Strong Jupiter placement indicates career success")
    if sun == 10:
        career["leadership"] = True
        strengths.append("Sun in 10th house - natural leadership abilities")
    if mercury in (3, 6, 10):
        career["communication"] = True
        strengths.append("Strong Mercury - excellent communication skills")

    fields = []
    if sun in (1, 5, 9):
        fields.append("Government/Leadership")
    if moon in (4, 7):
        fields.append("Public relations/Counseling")
    if mars in (3, 6, 10):
        fields.append("Engineering/Military/Sports")
    if mercury in (3, 6):
        fields.append("Writing/Teaching/Business")
    if jupiter in (5, 9):
        fields.append("Teaching/Law/Spiritual")
    if venus in (7, 11):
        fields.append("Arts/Creative/Finance")
    if saturn == 10:
        fields.append("Management/Administration")
    career["suggested_fields"] = fields[:3]

    # Relationships
    rel = signals["relationships"]
    if venus == 7:
        rel["focus"] = "high"
        strengths.append("Venus in 7th house - strong relationship potential")
    if venus in (1, 2, 3, 4, 5):
        rel["early_marriage"] = True
    if saturn == 7:
        rel["delayed_marriage"] = True
        rel["focus"] = "delayed but stable"
    if jupiter == 7 and venus in (2, 7):
        rel["multiple_marriages"] = "possible"

    # Spiritual
    spiritual = signals["spiritual"]
    if jupiter == 9:
        spiritual["growth"] = True
        strengths.append("Jupiter in 9th house - strong spiritual inclination")
    if ketu in (9, 12):
        spiritual["past_life"] = True
        strengths.append("Ketu in spiritual houses - past life spiritual practices")
    if rahu in (8, 12):
        spiritual["intense_quest"] = True

    # Health
    focus = signals["health"]["focus_areas"]
    if sun in (6, 8, 12):
        focus.append("Heart/Circulation")
    if moon in (6, 8):
        focus.append("Mind/Emotions")
    if mars in (6, 8):
        focus.append("Blood/Energy")
    if saturn in (6, 8):
        focus.append("Bones/Joints")
    if not focus:
        focus.append("General wellness")

    # Challenges (machine-readable codes live beside the human-readable text)
    challenges = signals["challenges"]
    codes: list[str] = []
    areas: list[str] = challenges["areas"]
    for condition, code, text in (
        (saturn == 1, "saturn", "Self-discipline and responsibility"),
        (saturn == 8, "saturn", "Transformational challenges"),
        (rahu == 8, "rahu", "Sudden changes and mysteries"),
        (ketu == 8, "ketu", "Letting go of attachments"),
        (mars == 8, "mars", "Managing anger and intensity"),
    ):
        if condition:
            areas.append(text)
            codes.append(code)
    challenges["codes"] = codes
    challenges["manglik"] = mars in MANGLIK_HOUSES
    if challenges["manglik"]:
        challenges["manglik_house"] = mars

    lucky = [f"House {n} ({p})" for n, p in ((jupiter, "Jupiter"), (venus, "Venus")) if n]
    strengths.append(f"Lucky areas: {', '.join(lucky)}")

    # Life purpose (first matching indicator wins)
    purpose = "Balanced personal development"
    for condition, text in (
        (sun in (1, 5, 9), "Self-expression and leadership"),
        (moon in (4, 7), "Nurturing and connecting with others"),
        (jupiter in (9, 12), "Wisdom and spiritual growth"),
        (saturn == 10, "Career achievement and discipline"),
        (rahu == 11, "Material success and innovation"),
    ):
        if condition:
            purpose = text
            break
    signals["life_purpose"] = purpose
    return signals


_REMEDIES = {
    "saturn": ("Saturn", "Serve elders, donate black items on Saturdays"),
    "rahu": ("Rahu", "Feed dogs, donate blankets, chant Rahu mantra"),
    "ketu": ("Ketu", "Spiritual practices, meditation, donate white items"),
    "mars": ("Mars", "Channel energy into exercise, recite Hanuman Chalisa on Tuesdays"),
}


def get_remedies(signals: dict[str, Any]) -> list[dict[str, str]]:
    remedies: list[dict[str, str]] = []
    challenges = signals["challenges"]
    if challenges.get("manglik"):
        remedies.append(
            {
                "type": "Manglik Dosha",
                "remedy": "Perform Hanuman Chalisa on Tuesdays, donate red items",
            }
        )
    for code in dict.fromkeys(challenges.get("codes", [])):
        kind, text = _REMEDIES[code]
        remedies.append({"type": kind, "remedy": text})
    for area in signals["health"]["focus_areas"]:
        if "Heart" in area:
            remedies.append(
                {
                    "type": "Heart Health",
                    "remedy": "Sun salutations, copper water, respect father/father figures",
                }
            )
        if "Mind" in area:
            remedies.append(
                {
                    "type": "Mental Peace",
                    "remedy": "Meditation, moon-related practices, cool foods",
                }
            )
    if not remedies:
        remedies.append(
            {
                "type": "General",
                "remedy": "Regular worship, charity, and positive thinking",
            }
        )
    return remedies
