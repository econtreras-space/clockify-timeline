# ADR-006: Daily Coverage Is Mandatory

## Status

Accepted

## Context

When a developer's EOD narrative describes less work than `productive_hours_per_day`, the reconstruction produces a proposal that totals fewer hours than the contracted workday. For example: a narrative describing 7h of explicit work, on a day configured for 8h productive hours, yields a 7h proposal — leaving one available gap unfilled.

This is incorrect behavior for a time-tracking tool. The developer was present and working for their full contracted day; the narrative just did not describe every minute in detail.

## Decision

Proposals must always cover the full `productive_hours_per_day` configured in `schedule_defaults.json`.

After the initial temporal distribution of narrative work units into blocks, the system must compute the remaining unallocated surface and distribute it proportionally across existing work blocks, weighted by `relative_weight`. Higher-weight blocks (those with stronger narrative support) absorb more of the expansion.

If the filled total is still short of `productive_hours_per_day` by more than ±0.25h, validation must emit a warning.

The only exception is when the user explicitly reports a shorter day (half-day, early departure, etc.) — in that case, the stated shorter duration is honoured.

## Consequences

- Proposals will consistently total `productive_hours_per_day`, matching what the user actually billed.
- Expanded blocks remain traceable to the narrative — they are stretched descriptions of real work, not invented tasks.
- This does not violate ADR-004 (Plausibility Over Precision): expanding described work is plausible distribution, not fabrication.
- This does not violate the "no fabricated work" rule: no new `WorkUnit` is invented; existing units are given proportionally more time.
- Users retain authority (ADR-001) to correct any expanded block duration during Stage 4 confirmation.
- Validation must enforce the coverage floor, not just a ceiling.
