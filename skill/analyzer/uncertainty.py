"""Confidence scoring and clarification trigger logic.

The analyzer uses this module to decide whether a WorkUnit or TimelineBlock
is supported well enough to proceed or whether clarification is needed first.

Governed by: docs/analyzer/uncertainty-model.md, docs/analyzer/clarification-loop.md
"""

from __future__ import annotations

from dataclasses import dataclass
from domain.types import AvailableGap, WorkUnit


@dataclass
class UncertaintySignal:
    source: str         # what caused uncertainty
    severity: float     # 0.0 (low concern) to 1.0 (must stop)
    message: str


def score_narrative_quality(raw_text: str) -> float:
    """
    Heuristic quality score for raw narrative text: 0.0 (empty/useless) to 1.0 (clear).

    This is intentionally simple in V1 — word count and keyword presence only.
    Replace with a proper LLM-based scorer in a later iteration.
    """
    if not raw_text or not raw_text.strip():
        return 0.0

    word_count = len(raw_text.split())
    if word_count < 5:
        return 0.2
    if word_count < 15:
        return 0.5
    if word_count < 40:
        return 0.75
    return 1.0


def score_work_unit(unit: WorkUnit) -> float:
    """Return a confidence score for a single WorkUnit."""
    base = 1.0
    if unit.ambiguity_markers:
        base -= 0.2 * len(unit.ambiguity_markers)
    if unit.relative_weight < 0.1:
        base -= 0.1
    return max(0.0, min(1.0, base))


def assess_allocation_surface(
    work_units: list[WorkUnit],
    available_gaps: list[AvailableGap],
) -> list[UncertaintySignal]:
    """Detect density or surface issues before temporal reconstruction begins."""
    signals: list[UncertaintySignal] = []
    total_gap_hours = sum(g.hours for g in available_gaps)

    if total_gap_hours <= 0:
        signals.append(UncertaintySignal(
            source="allocation_surface",
            severity=1.0,
            message="No available time gaps. Cannot allocate any work.",
        ))
        return signals

    # Rough estimate: assume 1–2h per work unit as a baseline expectation
    estimated_needed = len(work_units) * 1.0
    if estimated_needed > total_gap_hours * 1.2:
        signals.append(UncertaintySignal(
            source="density",
            severity=0.7,
            message=(
                f"{len(work_units)} work units against {total_gap_hours:.1f}h available. "
                "Day may be overloaded — some tasks will be compressed or merged."
            ),
        ))

    return signals


def should_clarify(signals: list[UncertaintySignal], narrative_score: float) -> bool:
    """Return True if the system should stop and ask before reconstructing."""
    if narrative_score < 0.3:
        return True
    if any(s.severity >= 1.0 for s in signals):
        return True
    high_severity = [s for s in signals if s.severity >= 0.7]
    if len(high_severity) >= 2:
        return True
    return False
