"""Formats a TimelineProposal into a human-readable review string.

Governed by: docs/prompts/proposal-generation.md
"""

from __future__ import annotations

from domain.types import TimelineProposal, ValidationOutcome


def format_proposal(proposal: TimelineProposal) -> str:
    """Return a review-friendly text representation of a TimelineProposal."""
    lines: list[str] = []
    date_str = proposal.report_date.strftime("%A, %B %-d %Y")
    lines.append(f"## Proposal for {date_str}\n")

    if not proposal.blocks:
        lines.append("No time blocks reconstructed.")
        return "\n".join(lines)

    for block in proposal.blocks:
        start = block.start.strftime("%H:%M")
        end = block.end.strftime("%H:%M")
        confidence_tag = f" _(low confidence)_" if block.confidence < 0.6 else ""
        lines.append(f"- **{start}–{end}** ({block.hours:.1f}h) {block.description}{confidence_tag}")

    lines.append(f"\n**Total:** {proposal.total_hours:.1f}h")

    if proposal.validation:
        v = proposal.validation
        if v.warnings:
            lines.append("\n### Warnings")
            for w in v.warnings:
                lines.append(f"- {w}")

        if v.outcome == ValidationOutcome.WARN:
            lines.append("\n_This proposal passed validation with warnings. Review before confirming._")
        elif v.outcome == ValidationOutcome.PASS:
            lines.append("\n_Proposal looks good. Confirm to push to Clockify._")

    return "\n".join(lines)


def format_clarification_request(proposal: TimelineProposal) -> str:
    """Return a targeted clarification prompt when the proposal cannot proceed."""
    if not proposal.validation or not proposal.validation.needs_clarification:
        return ""

    v = proposal.validation
    lines = ["I need a bit more context before I can reconstruct this day reliably.\n"]

    if v.clarification_questions:
        for q in v.clarification_questions:
            lines.append(f"- {q}")

    if v.warnings:
        lines.append("\nAdditional signals that need attention:")
        for w in v.warnings:
            lines.append(f"- {w}")

    lines.append(
        "\nPlease answer the questions above and I'll regenerate the proposal."
    )
    return "\n".join(lines)
