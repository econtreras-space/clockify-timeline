"""Applies the validation contract to a TimelineProposal.

Governed by: docs/prompts/validation-contract.md
"""

from __future__ import annotations

from domain.types import (
    AvailableGap,
    Constraint,
    ConstraintType,
    TimelineBlock,
    TimelineProposal,
    ValidationOutcome,
    ValidationState,
)

# Thresholds are intentionally loose for V1 — they will tighten after first iteration.
_MIN_CONFIDENCE_TO_PASS = 0.5
_MAX_DAILY_HOURS = 9.0      # hard ceiling; above this is implausible
_MIN_DAILY_HOURS = 0.5      # below this likely means empty narrative


def validate(
    proposal: TimelineProposal,
    available_gaps: list[AvailableGap],
    constraints: list[Constraint],
) -> ValidationState:
    """
    Return a ValidationState indicating whether the proposal may proceed.

    Outcomes:
    - PASS       → coherent, plausible, within constraints
    - WARN       → plausible but has notable weaknesses; user should review carefully
    - NEEDS_CLARIFICATION → not enough support to proceed; targeted questions generated
    - REJECT     → fundamentally invalid (invented missing day, constraint violation)
    """
    warnings: list[str] = []
    clarification_questions: list[str] = []

    # --- Rule 1: No invented missing days -----------------------------------
    # A proposal with zero blocks but a date means a missing workday was submitted.
    # This must be rejected, not silently accepted.
    if not proposal.blocks:
        return ValidationState(
            outcome=ValidationOutcome.REJECT,
            rejection_reason=(
                "Proposal contains no time blocks. The system must not fabricate "
                "a missing workday. Provide narrative context for this date or skip it."
            ),
        )

    total_hours = proposal.total_hours

    # --- Rule 2: Plausibility ceiling ---------------------------------------
    if total_hours > _MAX_DAILY_HOURS:
        return ValidationState(
            outcome=ValidationOutcome.REJECT,
            rejection_reason=(
                f"Proposal totals {total_hours:.1f}h which exceeds the plausible "
                f"maximum of {_MAX_DAILY_HOURS}h. The timeline is too dense to be believable."
            ),
        )

    # --- Rule 3: Minimum meaningful content ---------------------------------
    if total_hours < _MIN_DAILY_HOURS:
        clarification_questions.append(
            "The reconstructed day has very little work. "
            "Was there narrative context I missed, or should this day be skipped?"
        )
        return ValidationState(
            outcome=ValidationOutcome.NEEDS_CLARIFICATION,
            clarification_questions=clarification_questions,
        )

    # --- Rule 4: Constraint overlap check -----------------------------------
    hard_constraints = [c for c in constraints if c.is_hard and c.constraint_type != ConstraintType.WORKDAY_BOUNDARY]
    for block in proposal.blocks:
        for constraint in hard_constraints:
            if block.start < constraint.end and block.end > constraint.start:
                # Lunch break is excluded from provider but still a hard constraint
                if constraint.constraint_type == ConstraintType.LUNCH_BREAK:
                    return ValidationState(
                        outcome=ValidationOutcome.REJECT,
                        rejection_reason=(
                            f"Block '{block.description}' overlaps the lunch break "
                            f"({constraint.start.strftime('%H:%M')}–{constraint.end.strftime('%H:%M')}). "
                            "Lunch must be excluded from all proposals."
                        ),
                    )
                warnings.append(
                    f"Block '{block.description}' overlaps a hard constraint "
                    f"'{constraint.label}' ({constraint.start.strftime('%H:%M')}–"
                    f"{constraint.end.strftime('%H:%M')})."
                )

    # --- Rule 5: Low-confidence blocks --------------------------------------
    low_confidence_blocks = [b for b in proposal.blocks if b.confidence < _MIN_CONFIDENCE_TO_PASS]
    if len(low_confidence_blocks) > len(proposal.blocks) / 2:
        clarification_questions.append(
            "More than half the reconstructed blocks have low confidence. "
            "Can you describe what you worked on in more detail?"
        )
        return ValidationState(
            outcome=ValidationOutcome.NEEDS_CLARIFICATION,
            warnings=warnings,
            clarification_questions=clarification_questions,
        )
    elif low_confidence_blocks:
        for block in low_confidence_blocks:
            warnings.append(
                f"Block '{block.description}' has low confidence ({block.confidence:.0%}). "
                "Review before confirming."
            )

    # --- Rule 6: Blocks outside workday boundary ----------------------------
    workday = next(
        (c for c in constraints if c.constraint_type == ConstraintType.WORKDAY_BOUNDARY),
        None,
    )
    if workday:
        for block in proposal.blocks:
            if block.start < workday.start or block.end > workday.end:
                warnings.append(
                    f"Block '{block.description}' falls outside the configured workday "
                    f"({workday.start.strftime('%H:%M')}–{workday.end.strftime('%H:%M')})."
                )

    outcome = ValidationOutcome.WARN if warnings else ValidationOutcome.PASS
    return ValidationState(outcome=outcome, warnings=warnings)
