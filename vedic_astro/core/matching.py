"""Ashtakoota (Guna Milan) compatibility scoring and Manglik check."""

from __future__ import annotations

from typing import Any

import swisseph as swe

from .constants import (
    ENEMIES,
    FRIENDS,
    GANA,
    MANGLIK_HOUSES,
    NADI_BY_NAKSHATRA,
    NAKSHATRAS,
    RASHI_LORD,
    SIGNS,
    VARNA_BY_SIGN,
    VARNA_RANK,
    VASHYA_BY_SIGN,
    YONI,
    YONI_ENEMIES,
)
from .ephemeris import ascendant, house_of, moon_details, nakshatra_lord, sidereal_longitude
from .models import BirthData

MAX_SCORE = 36


def varna_koota(boy_rashi: int, girl_rashi: int) -> float:
    """1 point if the groom's varna is equal to or higher than the bride's."""
    boy = VARNA_RANK[VARNA_BY_SIGN[boy_rashi]]
    girl = VARNA_RANK[VARNA_BY_SIGN[girl_rashi]]
    return 1 if boy >= girl else 0


def vashya_koota(boy_rashi: int, girl_rashi: int) -> float:
    """Simplified: 2 for the same Vashya group, otherwise 1."""
    return 2 if VASHYA_BY_SIGN[boy_rashi] == VASHYA_BY_SIGN[girl_rashi] else 1


def tara_koota(boy_nak: int, girl_nak: int) -> float:
    """Count nakshatras both ways; remainders 3, 5, 7 (mod 9) are inauspicious."""

    def is_bad(src: int, dst: int) -> bool:
        return (((dst - src) % 27) + 1) % 9 in (3, 5, 7)

    bad = is_bad(boy_nak, girl_nak) + is_bad(girl_nak, boy_nak)
    return {0: 3, 1: 1.5, 2: 0}[bad]


def yoni_koota(boy_nak: int, girl_nak: int) -> float:
    """Simplified: same yoni 4, natural enemies 0, otherwise 2."""
    boy, girl = YONI[boy_nak], YONI[girl_nak]
    if boy == girl:
        return 4
    if frozenset((boy, girl)) in YONI_ENEMIES:
        return 0
    return 2


def _relation(a: str, b: str) -> str:
    if b in FRIENDS[a]:
        return "friend"
    if b in ENEMIES[a]:
        return "enemy"
    return "neutral"


def graha_maitri(boy_rashi: int, girl_rashi: int) -> float:
    lord_b, lord_g = RASHI_LORD[boy_rashi], RASHI_LORD[girl_rashi]
    if lord_b == lord_g:
        return 5
    pair = sorted((_relation(lord_b, lord_g), _relation(lord_g, lord_b)))
    return {
        ("friend", "friend"): 5,
        ("friend", "neutral"): 4,
        ("neutral", "neutral"): 3,
        ("enemy", "friend"): 1,
        ("enemy", "neutral"): 0.5,
        ("enemy", "enemy"): 0,
    }[tuple(pair)]


def gana_koota(boy_nak: int, girl_nak: int) -> float:
    boy, girl = GANA[boy_nak], GANA[girl_nak]
    if boy == girl:
        return 6
    table = {
        ("Manushya", "Deva"): 6,  # (boy, girl)
        ("Deva", "Manushya"): 5,
        ("Rakshasa", "Deva"): 1,
        ("Deva", "Rakshasa"): 0,
    }
    return table.get((boy, girl), 0)


def bhakoot_koota(boy_rashi: int, girl_rashi: int) -> float:
    """0 when the Moon signs stand 2/12, 5/9 or 6/8 from each other."""
    distance = ((girl_rashi - boy_rashi) % 12) + 1
    return 0 if distance in (2, 12, 5, 9, 6, 8) else 7


def nadi_koota(boy_nak: int, girl_nak: int) -> float:
    return 8 if NADI_BY_NAKSHATRA[boy_nak] != NADI_BY_NAKSHATRA[girl_nak] else 0


def compatibility_band(total: float) -> str:
    if total >= 32:
        return "Excellent"
    if total >= 28:
        return "Very Good"
    if total >= 24:
        return "Good"
    if total >= 18:
        return "Average"
    if total >= 12:
        return "Below Average"
    return "Not Recommended"


def _person(birth: BirthData) -> dict[str, Any]:
    jd = birth.julian_day
    nak, rashi, _ = moon_details(jd)
    asc = ascendant(jd, birth.latitude, birth.longitude)["longitude"]
    mars = sidereal_longitude(jd, swe.MARS)
    mars_house = house_of(mars, asc)
    return {
        "nakshatra": NAKSHATRAS[nak],
        "nakshatra_index": nak,
        "nakshatra_lord": nakshatra_lord(nak),
        "rashi": rashi,
        "rashi_name": SIGNS[rashi],
        "gana": GANA[nak],
        "yoni": YONI[nak],
        "nadi": NADI_BY_NAKSHATRA[nak],
        "manglik": mars_house in MANGLIK_HOUSES,
        "manglik_house": mars_house,
    }


def match_kundalis(boy: BirthData, girl: BirthData) -> dict[str, Any]:
    b, g = _person(boy), _person(girl)
    scores = {
        "Varna": varna_koota(b["rashi"], g["rashi"]),
        "Vashya": vashya_koota(b["rashi"], g["rashi"]),
        "Tara": tara_koota(b["nakshatra_index"], g["nakshatra_index"]),
        "Yoni": yoni_koota(b["nakshatra_index"], g["nakshatra_index"]),
        "Graha Maitri": graha_maitri(b["rashi"], g["rashi"]),
        "Gana": gana_koota(b["nakshatra_index"], g["nakshatra_index"]),
        "Bhakoot": bhakoot_koota(b["rashi"], g["rashi"]),
        "Nadi": nadi_koota(b["nakshatra_index"], g["nakshatra_index"]),
    }
    total = sum(scores.values())
    result: dict[str, Any] = {
        "scores": scores,
        "total": total,
        "max_score": MAX_SCORE,
        "compatibility": compatibility_band(total),
        "boy": b,
        "girl": g,
    }
    if b["manglik"] != g["manglik"]:
        result["manglik_dosha"] = "Present - One partner is manglik while the other is not"
        result["manglik_remedy"] = (
            "Consider performing manglik shanti puja or matching with another manglik"
        )
    else:
        result["manglik_dosha"] = "Cancelled - Both partners have similar manglik status"
    return result
