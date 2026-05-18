"""Calendar adapter — converts external calendar events into Constraint data.

Stub for V1. Real calendar integration (Google Calendar, iCal) goes here.
The adapter translates calendar events into the internal Constraint format
so the constraint_builder can include them without knowing the source.

Governed by: docs/providers/calendar-provider.md, ADR-005
"""

from __future__ import annotations

from datetime import date

from domain.types import Constraint


def fetch_constraints_for_date(report_date: date) -> list[Constraint]:
    """Return calendar-derived constraints for the given date.

    V1: Returns empty list. Calendar integration is a future milestone.
    When implemented, this should return only hard anchors (confirmed meetings)
    and leave advisory events as warnings rather than hard constraints.
    """
    return []
