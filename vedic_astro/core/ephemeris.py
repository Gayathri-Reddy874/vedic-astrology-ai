"""Sidereal chart calculation on top of the Swiss Ephemeris (Lahiri ayanamsa).

All longitudes returned here are sidereal. The Moshier ephemeris is used so the
app needs no external ephemeris data files.
"""

from __future__ import annotations

from typing import Any

import swisseph as swe

from .constants import (
    FIXED_KARANAS,
    MOVABLE_KARANAS,
    NAKSHATRA_LORDS,
    NAKSHATRAS,
    PLANET_SYMBOLS,
    SIGNS,
    SIGNS_EN,
    TITHIS,
    YOGAS,
)
from .models import BirthData

swe.set_sid_mode(swe.SIDM_LAHIRI)

_FLAGS = swe.FLG_SIDEREAL | swe.FLG_MOSEPH | swe.FLG_SPEED
_NAKSHATRA_SPAN = 360 / 27

PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
}


def sign_index(longitude: float) -> int:
    return int((longitude % 360) // 30)


def zodiac(longitude: float) -> tuple[str, str, float]:
    """Return (sanskrit sign, english sign, degree within the sign)."""
    longitude %= 360
    idx = sign_index(longitude)
    return SIGNS[idx], SIGNS_EN[idx], round(longitude % 30, 2)


def nakshatra_of(longitude: float) -> tuple[int, str, int]:
    """Return (index, name, pada 1-4) for a sidereal longitude."""
    position = (longitude % 360) / _NAKSHATRA_SPAN
    index = min(int(position), 26)
    pada = min(int((position - index) * 4) + 1, 4)
    return index, NAKSHATRAS[index], pada


def house_of(longitude: float, ascendant_longitude: float) -> int:
    """Whole-sign house (1-12) of a longitude relative to the Lagna."""
    return (sign_index(longitude) - sign_index(ascendant_longitude)) % 12 + 1


def _planet_entry(name: str, longitude: float, retrograde: bool) -> dict[str, Any]:
    sign, sign_en, degree = zodiac(longitude)
    _, nak, pada = nakshatra_of(longitude)
    return {
        "longitude": round(longitude % 360, 3),
        "sign": sign,
        "sign_en": sign_en,
        "degree": degree,
        "nakshatra": nak,
        "pada": pada,
        "retrograde": retrograde,
        "symbol": PLANET_SYMBOLS.get(name, ""),
    }


def planet_positions(jd: float) -> dict[str, dict[str, Any]]:
    data: dict[str, dict[str, Any]] = {}
    for name, body in PLANETS.items():
        values, _ = swe.calc_ut(jd, body, _FLAGS)
        longitude, speed = values[0], values[3]
        retrograde = speed < 0 and name not in ("Sun", "Moon")
        data[name] = _planet_entry(name, longitude, retrograde=retrograde)
    rahu_values, _ = swe.calc_ut(jd, swe.MEAN_NODE, _FLAGS)
    rahu = rahu_values[0] % 360
    data["Rahu"] = _planet_entry("Rahu", rahu, retrograde=True)
    data["Ketu"] = _planet_entry("Ketu", (rahu + 180) % 360, retrograde=True)
    return data


def ascendant(jd: float, latitude: float, longitude: float) -> dict[str, Any]:
    """Sidereal ascendant (tropical Asc minus the Lahiri ayanamsa)."""
    _, ascmc = swe.houses(jd, latitude, longitude)
    sidereal = (ascmc[0] - swe.get_ayanamsa_ut(jd)) % 360
    sign, sign_en, degree = zodiac(sidereal)
    return {"longitude": round(sidereal, 3), "sign": sign, "sign_en": sign_en, "degree": degree}


def house_system(ascendant_longitude: float) -> dict[str, dict[str, Any]]:
    """Equal/whole-sign houses counted from the Lagna (standard in Jyotish)."""
    result = {}
    for i in range(12):
        sign, sign_en, degree = zodiac(ascendant_longitude + 30 * i)
        result[f"House {i + 1}"] = {"sign": sign, "sign_en": sign_en, "degree": degree}
    return result


def tithi_from_longitudes(sun: float, moon: float) -> dict[str, Any]:
    diff = (moon - sun) % 360
    index = int(diff // 12)
    return {
        "Tithi": TITHIS[index],
        "Tithi_Index": index + 1,
        "Paksha": "Shukla" if index < 15 else "Krishna",
    }


def karana_from_longitudes(sun: float, moon: float) -> str:
    index = int(((moon - sun) % 360) // 6)
    if index in FIXED_KARANAS:
        return FIXED_KARANAS[index]
    return MOVABLE_KARANAS[(index - 1) % 7]


def yoga_from_longitudes(sun: float, moon: float) -> str:
    return YOGAS[int(((sun + moon) % 360) // _NAKSHATRA_SPAN)]


def panchanga(jd: float) -> dict[str, Any]:
    sun = swe.calc_ut(jd, swe.SUN, _FLAGS)[0][0]
    moon = swe.calc_ut(jd, swe.MOON, _FLAGS)[0][0]
    _, nak, pada = nakshatra_of(moon)
    return {
        **tithi_from_longitudes(sun, moon),
        "Nakshatra": nak,
        "Pada": pada,
        "Yoga": yoga_from_longitudes(sun, moon),
        "Karana": karana_from_longitudes(sun, moon),
    }


def sidereal_longitude(jd: float, body: int) -> float:
    return swe.calc_ut(jd, body, _FLAGS)[0][0]


def moon_details(jd: float) -> tuple[int, int, float]:
    """Return (nakshatra index, rashi index, sidereal Moon longitude)."""
    moon = swe.calc_ut(jd, swe.MOON, _FLAGS)[0][0]
    return nakshatra_of(moon)[0], sign_index(moon), moon


def nakshatra_lord(index: int) -> str:
    return NAKSHATRA_LORDS[index]


def build_chart(birth: BirthData) -> dict[str, Any]:
    """Compute the complete horoscope for a validated :class:`BirthData`."""
    jd = birth.julian_day
    asc = ascendant(jd, birth.latitude, birth.longitude)
    return {
        "Ascendant": asc,
        "Planets": planet_positions(jd),
        "Houses": house_system(asc["longitude"]),
        "Panchanga": panchanga(jd),
        "JulianDay": jd,
    }
