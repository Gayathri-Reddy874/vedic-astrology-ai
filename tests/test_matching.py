import pytest

from vedic_astro.core import matching as m
from vedic_astro.core.models import BirthData


def person(y, mo, d, hour=12):
    return BirthData(y, mo, d, hour, 0, 0, 12.97, 77.59, 5.5)


def test_identical_charts_score_expected_total():
    result = m.match_kundalis(person(1995, 5, 10), person(1995, 5, 10))
    assert result["scores"]["Nadi"] == 0  # same nadi never scores
    assert result["scores"]["Gana"] == 6 and result["scores"]["Yoni"] == 4
    assert result["total"] == 28
    assert result["manglik_dosha"].startswith("Cancelled")


def test_total_never_exceeds_maximum_and_matches_band():
    result = m.match_kundalis(person(1992, 3, 1), person(1996, 11, 25))
    assert 0 <= result["total"] <= 36
    assert result["compatibility"] == m.compatibility_band(result["total"])
    assert set(result["scores"]) == {
        "Varna",
        "Vashya",
        "Tara",
        "Yoni",
        "Graha Maitri",
        "Gana",
        "Bhakoot",
        "Nadi",
    }


@pytest.mark.parametrize(
    "boy, girl, expected",
    [(0, 0, 7), (0, 1, 0), (0, 4, 0), (0, 5, 0), (0, 2, 7), (0, 3, 7), (0, 7, 0), (0, 11, 0)],
)
def test_bhakoot_distances(boy, girl, expected):
    assert m.bhakoot_koota(boy, girl) == expected


def test_nadi_requires_different_nadi():
    assert m.nadi_koota(0, 0) == 0  # Ashwini / Ashwini (Adi, Adi)
    assert m.nadi_koota(0, 1) == 8  # Adi / Madhya


def test_gana_asymmetry():
    deva, manushya, rakshasa = 0, 1, 2  # Ashwini, Bharani, Krittika
    assert m.gana_koota(manushya, deva) == 6
    assert m.gana_koota(deva, manushya) == 5
    assert m.gana_koota(rakshasa, deva) == 1
    assert m.gana_koota(deva, rakshasa) == 0


def test_graha_maitri_friend_enemy_cases():
    assert m.graha_maitri(0, 7) == 5  # both ruled by Mars
    assert m.graha_maitri(4, 0) == 5  # Sun / Mars friends
    assert m.graha_maitri(4, 1) == 0  # Sun / Venus enemies


def test_tara_scores_are_discrete():
    # With mutual counting the two remainders always sum to 2 (mod 9), so "both
    # inauspicious" (0 points) cannot occur; only 3 and 1.5 are reachable.
    values = {m.tara_koota(a, b) for a in range(27) for b in range(27)}
    assert values == {1.5, 3}


def test_yoni_enemy_pairs_score_zero():
    horse, buffalo = 0, 12  # Ashwini, Hasta
    assert m.yoni_koota(horse, buffalo) == 0
