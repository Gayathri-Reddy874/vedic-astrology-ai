"""Typed input models with validation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import swisseph as swe

from .errors import ValidationError


def _number(data: Mapping[str, Any], key: str, *, default: float | None = None) -> float:
    raw = data.get(key)
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        if default is None:
            raise ValidationError(f"'{key}' is required.")
        return default
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"'{key}' must be a number.") from exc
    if value != value or value in (float("inf"), float("-inf")):
        raise ValidationError(f"'{key}' must be a finite number.")
    return value


@dataclass(frozen=True)
class BirthData:
    """Validated birth details. ``timezone`` is the offset from UTC in hours."""

    year: int
    month: int
    day: int
    hour: int = 12
    minute: int = 0
    second: int = 0
    latitude: float = 0.0
    longitude: float = 0.0
    timezone: float = 5.5
    name: str = ""

    def __post_init__(self) -> None:
        if not 1 <= self.year <= 9999:
            raise ValidationError("Year must be between 1 and 9999.")
        if not -90 <= self.latitude <= 90:
            raise ValidationError("Latitude must be between -90 and 90.")
        if not -180 <= self.longitude <= 180:
            raise ValidationError("Longitude must be between -180 and 180.")
        if not -12 <= self.timezone <= 14:
            raise ValidationError("Timezone offset must be between -12 and +14 hours.")
        try:
            _ = self.local_datetime
        except ValueError as exc:
            raise ValidationError(f"Invalid date or time: {exc}.") from exc

    @property
    def local_datetime(self) -> datetime:
        return datetime(self.year, self.month, self.day, self.hour, self.minute, self.second)

    @property
    def utc_datetime(self) -> datetime:
        return self.local_datetime - timedelta(hours=self.timezone)

    @property
    def julian_day(self) -> float:
        u = self.utc_datetime
        decimal_hour = u.hour + u.minute / 60 + u.second / 3600
        return swe.julday(u.year, u.month, u.day, decimal_hour)

    @classmethod
    def from_mapping(
        cls,
        data: Mapping[str, Any],
        *,
        prefix: str = "",
        default_hour: float | None = None,
    ) -> BirthData:
        """Build from a form/JSON mapping.

        Date/time keys are read with ``prefix`` (e.g. ``boy_year``); location and
        timezone keys are shared and never prefixed.
        """
        year = int(_number(data, f"{prefix}year"))
        month = int(_number(data, f"{prefix}month"))
        day = int(_number(data, f"{prefix}day"))
        if default_hour is None:
            hour = _number(data, f"{prefix}hour")
        else:
            hour = _number(data, f"{prefix}hour", default=default_hour)
        minute = _number(data, f"{prefix}minute", default=0)
        second = _number(data, f"{prefix}second", default=0)
        total_seconds = round(hour * 3600 + minute * 60 + second)
        if not 0 <= hour < 24 or not 0 <= minute < 60 or not 0 <= second < 60:
            raise ValidationError("Time must be a valid 24-hour clock value.")
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        name = str(data.get(f"{prefix}name", data.get("name", "")) or "").strip()[:80]
        return cls(
            year=year,
            month=month,
            day=day,
            hour=min(hours, 23),
            minute=minutes,
            second=seconds,
            latitude=_number(data, "latitude"),
            longitude=_number(data, "longitude"),
            timezone=_number(data, "timezone", default=5.5),
            name=name,
        )
