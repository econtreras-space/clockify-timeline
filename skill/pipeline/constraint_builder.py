"""Builds Constraint and AvailableGap lists from schedule config + optional calendar data."""

from __future__ import annotations

import json
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from domain.types import AvailableGap, Constraint, ConstraintType

_CONFIG_PATH = Path(__file__).parent.parent / "config" / "schedule_defaults.json"


def _load_config(config_path: Path = _CONFIG_PATH) -> dict:
    with open(config_path) as f:
        return json.load(f)


def _parse_time(time_str: str, report_date: date, timezone: str) -> datetime:
    """Parse HH:MM string into a timezone-aware datetime on the given date."""
    import zoneinfo
    tz = zoneinfo.ZoneInfo(timezone)
    h, m = map(int, time_str.split(":"))
    return datetime(report_date.year, report_date.month, report_date.day, h, m, tzinfo=tz)


def build_constraints(
    report_date: date,
    timezone: Optional[str] = None,
    config_path: Path = _CONFIG_PATH,
    extra_constraints: Optional[list[dict]] = None,
) -> list[Constraint]:
    """Return all hard constraints for the given day."""
    config = _load_config(config_path)
    tz = timezone or config["workday"]["timezone"]
    constraints: list[Constraint] = []

    # Workday boundary
    constraints.append(Constraint(
        constraint_type=ConstraintType.WORKDAY_BOUNDARY,
        start=_parse_time(config["workday"]["start"], report_date, tz),
        end=_parse_time(config["workday"]["end"], report_date, tz),
        label="Workday",
        origin="schedule_config",
        is_hard=True,
    ))

    for item in config.get("fixed_constraints", []):
        constraints.append(Constraint(
            constraint_type=ConstraintType(item["type"]),
            start=_parse_time(item["start"], report_date, tz),
            end=_parse_time(item["end"], report_date, tz),
            label=item["label"],
            origin="schedule_config",
            is_hard=item.get("is_hard", True),
        ))

    for item in (extra_constraints or []):
        constraints.append(Constraint(
            constraint_type=ConstraintType(item.get("type", "calendar_anchor")),
            start=_parse_time(item["start"], report_date, tz),
            end=_parse_time(item["end"], report_date, tz),
            label=item.get("label", "External"),
            origin=item.get("origin", "calendar"),
            is_hard=item.get("is_hard", False),
        ))

    return constraints


def build_available_gaps(
    report_date: date,
    timezone: Optional[str] = None,
    config_path: Path = _CONFIG_PATH,
) -> list[AvailableGap]:
    """Return the pre-defined allocatable time surfaces for the given day."""
    config = _load_config(config_path)
    tz = timezone or config["workday"]["timezone"]
    return [
        AvailableGap(
            start=_parse_time(gap["start"], report_date, tz),
            end=_parse_time(gap["end"], report_date, tz),
        )
        for gap in config.get("available_gaps", [])
    ]
