import pytest

from vedic_astro.core import ephemeris as eph
from vedic_astro.core.models import BirthData

from .conftest import BIRTH


@pytest.fixture(scope="module")
def chart():
    return eph.build_chart(BirthData.from_mapping(BIRTH))


def test_nakshatra_boundaries():
    assert eph.nakshatra_of(0) == (0, "Ashwini", 1)
    assert eph.nakshatra_of(13.34)[1:] == ("Bharani", 1)
    assert eph.nakshatra_of(359.99) == (26, "Revati", 4)


def test_zodiac_wraps_and_rounds():
    assert eph.zodiac(0)[:2] == ("Mesha", "Aries")
    assert eph.zodiac(359.5)[:2] == ("Meena", "Pisces")
    assert eph.zodiac(45.123)[2] == 15.12


def test_sun_is_sidereal_not_tropical(chart):
    # 2000-01-01 04:00 UTC: tropical Sun ~280.4, Lahiri ayanamsa ~23.86 -> ~256.5
    assert 255.5 < chart["Planets"]["Sun"]["longitude"] < 257.5
    assert chart["Planets"]["Sun"]["sign"] == "Dhanu"


def test_nodes_are_sidereal_and_opposite(chart):
    rahu, ketu = chart["Planets"]["Rahu"], chart["Planets"]["Ketu"]
    assert 99 < rahu["longitude"] < 104  # tropical mean node ~125 minus ayanamsa
    assert abs(((ketu["longitude"] - rahu["longitude"]) % 360) - 180) < 0.01
    assert rahu["retrograde"] and ketu["retrograde"]


def test_houses_are_consecutive_from_lagna(chart):
    asc_sign = chart["Ascendant"]["sign"]
    assert chart["Houses"]["House 1"]["sign"] == asc_sign
    signs = [chart["Houses"][f"House {i}"]["sign"] for i in range(1, 13)]
    assert len(set(signs)) == 12


def test_ascendant_matches_expected_lagna(chart):
    # Bengaluru, ~10:30 IST in January: Kumbha (Aquarius) lagna.
    assert chart["Ascendant"]["sign"] == "Kumbha"


def test_tithi_paksha_boundaries():
    assert eph.tithi_from_longitudes(0, 0)["Tithi"] == "Pratipada"
    assert eph.tithi_from_longitudes(0, 179)["Tithi"] == "Purnima"
    krishna = eph.tithi_from_longitudes(0, 181)
    assert krishna["Paksha"] == "Krishna" and krishna["Tithi_Index"] == 16
    assert eph.tithi_from_longitudes(0, 359)["Tithi"] == "Amavasya"


def test_karana_and_yoga_sequences():
    assert eph.karana_from_longitudes(0, 0) == "Kimstughna"
    assert eph.karana_from_longitudes(0, 6.5) == "Bava"
    assert eph.karana_from_longitudes(0, 345) == "Shakuni"
    assert eph.karana_from_longitudes(0, 352) == "Chatushpada"
    assert eph.karana_from_longitudes(0, 358) == "Naga"
    assert eph.yoga_from_longitudes(0, 0) == "Vishkambha"
    assert eph.yoga_from_longitudes(180, 179.9) == "Vaidhriti"


def test_timezone_conversion_crosses_midnight():
    late = BirthData(2000, 1, 1, 1, 0, 0, 0, 0, timezone=5.5)
    utc = late.utc_datetime
    assert (utc.year, utc.month, utc.day) == (1999, 12, 31)
    assert late.utc_datetime.hour == 19 and late.utc_datetime.minute == 30
