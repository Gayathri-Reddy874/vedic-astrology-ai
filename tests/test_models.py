import pytest

from vedic_astro.core.errors import ValidationError
from vedic_astro.core.models import BirthData

from .conftest import BIRTH


def test_valid_form_strings_are_parsed():
    form = {k: str(v) for k, v in BIRTH.items()} | {"name": "  Asha  "}
    birth = BirthData.from_mapping(form)
    assert (birth.year, birth.hour, birth.minute) == (2000, 10, 30)
    assert birth.name == "Asha"


def test_fractional_hour_becomes_minutes():
    birth = BirthData.from_mapping(BIRTH | {"hour": 10.5, "minute": 0})
    assert (birth.hour, birth.minute) == (10, 30)


@pytest.mark.parametrize(
    "patch, fragment",
    [
        ({"latitude": 91}, "Latitude"),
        ({"longitude": -181}, "Longitude"),
        ({"timezone": 20}, "Timezone"),
        ({"month": 13}, "Invalid date"),
        ({"day": 31, "month": 2}, "Invalid date"),
        ({"hour": 24}, "24-hour"),
        ({"minute": 60}, "24-hour"),
        ({"year": "abc"}, "number"),
        ({"latitude": "nan"}, "finite"),
    ],
)
def test_invalid_input_is_rejected(patch, fragment):
    with pytest.raises(ValidationError, match=fragment):
        BirthData.from_mapping(BIRTH | patch)


def test_missing_required_field():
    data = {k: v for k, v in BIRTH.items() if k != "latitude"}
    with pytest.raises(ValidationError, match="latitude"):
        BirthData.from_mapping(data)


def test_prefixed_fields_share_location():
    form = {
        "boy_year": 1995,
        "boy_month": 5,
        "boy_day": 10,
        "girl_year": 1997,
        "girl_month": 8,
        "girl_day": 20,
        "latitude": 12.9,
        "longitude": 77.6,
    }
    boy = BirthData.from_mapping(form, prefix="boy_", default_hour=12)
    girl = BirthData.from_mapping(form, prefix="girl_", default_hour=12)
    assert (boy.year, girl.year, boy.hour, girl.latitude) == (1995, 1997, 12, 12.9)
