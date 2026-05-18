"""Translates an accepted TimelineProposal into a ProviderPayload for Clockify.

This is the adapter boundary. Clockify-specific formatting lives here and
nowhere else in the system. Internal domain types must not be shaped by
Clockify requirements.

Governed by: docs/providers/clockify-adapter.md, ADR-002
"""

from __future__ import annotations

from domain.types import ClockifyEntry, ConstraintType, ProviderPayload, TimelineProposal


def to_provider_payload(
    proposal: TimelineProposal,
    exclude_types: set[str] | None = None,
) -> ProviderPayload:
    """
    Convert an accepted TimelineProposal into a Clockify-ready ProviderPayload.

    Blocks that correspond to excluded constraint types (e.g. lunch_break) are
    dropped here at the adapter boundary — not earlier.
    """
    if not proposal.is_confirmed:
        raise ValueError(
            "Cannot translate a proposal that has not passed validation. "
            "Call validate() and get user confirmation before this step."
        )

    excluded_labels = _build_excluded_labels(exclude_types or {"lunch_break"})
    entries: list[ClockifyEntry] = []

    for block in proposal.blocks:
        if block.description.lower() in excluded_labels:
            continue
        entries.append(ClockifyEntry(
            date=proposal.report_date.isoformat(),
            start=block.start.strftime("%H:%M"),
            end=block.end.strftime("%H:%M"),
            description=block.description,
            hours=round(block.hours, 2),
        ))

    return ProviderPayload(
        provider="clockify",
        entries=entries,
        metadata={
            "report_date": proposal.report_date.isoformat(),
            "total_hours": round(sum(e.hours for e in entries), 2),
            "entry_count": len(entries),
        },
        submission_ready=True,
    )


def payload_to_json_dict(payload: ProviderPayload) -> dict:
    """Serialize a ProviderPayload to the dict format expected by push_clockify.py."""
    return {
        "entries": [
            {
                "date": e.date,
                "start": e.start,
                "end": e.end,
                "description": e.description,
                "hours": e.hours,
            }
            for e in payload.entries
        ],
        "summary": {
            "total_days": len({e.date for e in payload.entries}),
            "total_hours": payload.metadata.get("total_hours", 0),
            "date_range": _date_range(payload),
        },
    }


def _build_excluded_labels(exclude_types: set[str]) -> set[str]:
    label_map = {
        "lunch_break": {"lunch", "lunch break"},
    }
    excluded: set[str] = set()
    for t in exclude_types:
        excluded.update(label_map.get(t, set()))
    return excluded


def _date_range(payload: ProviderPayload) -> str:
    if not payload.entries:
        return ""
    dates = sorted(e.date for e in payload.entries)
    return f"{dates[0]} to {dates[-1]}"
