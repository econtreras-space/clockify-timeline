"""Distributes WorkUnits into plausible TimelineBlocks within AvailableGaps.

This module documents the reconstruction contract and provides the prompt
template that Claude uses when invoked as the reconstructor in Stage 2.

Governed by: docs/prompts/analyzer-contract.md, docs/analyzer/temporal-reconstruction.md
"""

from __future__ import annotations

from datetime import datetime, timedelta

from analyzer.uncertainty import score_work_unit
from domain.types import AvailableGap, Constraint, ConstraintType, TimelineBlock, WorkUnit

# ---------------------------------------------------------------------------
# Prompt template — injected into the Claude reasoning step in SKILL.md Stage 2
# ---------------------------------------------------------------------------

RECONSTRUCTION_PROMPT = """
You are the Temporal Reconstructor stage of a timesheet reconstruction system.

Your job: distribute the work units below into plausible time blocks within the available gaps.
You are ALLOCATING time, not OBSERVING it. Every block you produce is a reconstruction, not a fact.

Rules:
- Use only the available gaps listed. Do not create blocks outside them.
- Do not overlap any hard constraint.
- Respect human continuity: avoid robotic 30-min splits unless the work genuinely calls for it.
- Preserve operational noise: meetings, context-switching, and coordination overhead are real.
- Use relative_weight to guide time allocation — heavier tasks get more time.
- If work units exceed the available surface, compress lower-weight tasks or note the overflow.
- Add a short trace note explaining why each block has its allocated duration.

Available gaps (each is an allocatable surface):
{gaps}

Hard constraints (must not be overlapped):
{constraints}

Work units to distribute:
{work_units}

Output format (JSON array of time blocks):
[
  {{
    "start": "HH:MM",
    "end": "HH:MM",
    "description": "...",
    "work_unit_index": 0,
    "confidence": 0.0,
    "trace": "..."
  }}
]

Date: {date}
""".strip()


def build_reconstruction_prompt(
    work_units: list[WorkUnit],
    available_gaps: list[AvailableGap],
    constraints: list[Constraint],
    report_date: str,
) -> str:
    """Return the prompt string to send to Claude for temporal reconstruction."""
    gaps_text = "\n".join(
        f"  - {g.start.strftime('%H:%M')}–{g.end.strftime('%H:%M')} ({g.hours:.1f}h)"
        for g in available_gaps
    )
    hard = [c for c in constraints if c.is_hard and c.constraint_type != ConstraintType.WORKDAY_BOUNDARY]
    constraints_text = "\n".join(
        f"  - {c.label}: {c.start.strftime('%H:%M')}–{c.end.strftime('%H:%M')}"
        for c in hard
    ) or "  (none beyond workday boundary)"
    units_text = "\n".join(
        f"  {i}. [{unit.category.value}] {unit.description} "
        f"(weight={unit.relative_weight:.1f}"
        + (f", ambiguous: {', '.join(unit.ambiguity_markers)}" if unit.ambiguity_markers else "")
        + ")"
        for i, unit in enumerate(work_units)
    )

    return RECONSTRUCTION_PROMPT.format(
        gaps=gaps_text,
        constraints=constraints_text,
        work_units=units_text,
        date=report_date,
    )


def parse_reconstruction_response(
    response: list[dict],
    work_units: list[WorkUnit],
    report_date_str: str,
    timezone: str,
) -> list[TimelineBlock]:
    """Convert Claude's JSON response into typed TimelineBlock objects."""
    import zoneinfo
    from datetime import date as dt_date

    tz = zoneinfo.ZoneInfo(timezone)
    year, month, day = map(int, report_date_str.split("-"))
    blocks: list[TimelineBlock] = []

    for item in response:
        h_start, m_start = map(int, item["start"].split(":"))
        h_end, m_end = map(int, item["end"].split(":"))
        start_dt = datetime(year, month, day, h_start, m_start, tzinfo=tz)
        end_dt = datetime(year, month, day, h_end, m_end, tzinfo=tz)

        unit_idx = item.get("work_unit_index")
        work_unit = work_units[unit_idx] if unit_idx is not None and unit_idx < len(work_units) else None
        confidence = float(item.get("confidence", 1.0))
        if work_unit:
            confidence = min(confidence, score_work_unit(work_unit))

        blocks.append(TimelineBlock(
            start=start_dt,
            end=end_dt,
            description=item["description"],
            work_unit_ref=work_unit,
            confidence=confidence,
            trace=item.get("trace", ""),
        ))

    return blocks
