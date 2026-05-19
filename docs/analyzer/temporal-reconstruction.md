# Temporal Reconstruction

## Primary Question

How does the analyzer turn `WorkUnit` meaning into plausible `TimelineBlock` allocations?

## Role

Temporal reconstruction is the stage where semantic work is mapped into time.

It takes the output of semantic extraction and projects it into the real structure of the day using:

- `Constraint` data,
- `AvailableGap` regions,
- operational noise assumptions,
- and uncertainty-aware reasoning.

## Canonical Concepts

This phase manipulates a small set of internal concepts:

- `Constraint`: hard boundaries that must be respected
- `AvailableGap`: allocatable time surfaces left after constraints are applied
- operational noise allowance: realism-preserving reserved flexibility
- `TimelineBlock`: individual reconstructed time block
- `TimelineProposal`: the full day-level proposal composed of blocks

## Reconstruction Principles

Temporal reconstruction is interpretive and plausibility-driven, not empirical tracking.

It should:

- respect hard constraints
- avoid impossible density
- preserve enough continuity to feel human
- keep the output easy to review and correct

It should not pretend that the result is a factual recording of observed activity.

## Explicit Hour Budgets

When the narrative contains explicit per-project hour statements (e.g. "Hours: 3.5 hs" under a project section), those values become **hard budgets** that override proportional allocation. The schedule gaps determine only *where* blocks are placed, not *how long* they are.

When a project has an explicit budget, its `AvailableGap` surface is `budget - constraint_hours`, where `constraint_hours` is the sum of any constraint blocks attributed to that project via the schedule config's `project_key` field. The remaining gap allocation covers the balance of the budget exactly.

If the sum of all stated budgets falls below `productive_hours_per_day`, the gap is reported as `shortfall_hours` — an informational note, not an error. Blocks are never expanded to fill it.

## Coverage Target

`productive_hours_per_day` is a configurable target surface, not a mandatory fill command.

Available gap surface = configured work surface minus fixed constraints. If narrative work units account for less than that surface after initial distribution, the analyzer may expand already-described work proportionally using `relative_weight` when that still feels like a plausible continuation of the same day.

This expansion is optional and bounded:

- it must stay attached to described work
- it must not force every day to reach the configured target
- it must yield to explicit user-stated hours when present
- it must yield to uncertainty and clarification when support is weak

Shorter valid days are acceptable when the narrative support is meaningfully partial or when the user clearly states their hours.

## How Reconstruction Proceeds

At a high level, the phase should:

1. take the candidate `WorkUnit` set
2. understand which `AvailableGap` regions can still accept allocation
3. reserve enough realism for fragmentation and non-visible work
4. distribute work into `TimelineBlock` candidates
5. assemble a coherent `TimelineProposal`

This is the phase where semantic-to-temporal translation becomes concrete, but it must remain bounded by [Uncertainty Model](./uncertainty-model.md) signals and [Clarification Loop](./clarification-loop.md) triggers.

## Compact Example

Given:

- `WorkUnit`: sync implementation
- `WorkUnit`: PR review
- `Constraint`: 10:00-10:30 daily
- `Constraint`: 12:30-13:00 lunch
- `AvailableGap`: 09:00-10:00, 10:30-12:30, 13:00-17:00

A plausible reconstruction might produce:

- `TimelineBlock`: 09:00-10:00 PR review
- `TimelineBlock`: 10:30-12:00 sync implementation
- `TimelineBlock`: 13:00-15:30 sync implementation

This is plausible because it respects hard boundaries and preserves continuity. It is not claiming the system observed those exact times.

## Hand-off

The result of this phase is a `TimelineProposal` containing `TimelineBlock` allocations plus the corresponding `Validation/Confidence State`.

If the proposal is too compressed, contradictory, or weakly supported, this phase should hand control toward:

- [Uncertainty Model](./uncertainty-model.md),
- [Clarification Loop](./clarification-loop.md),
- or [Failure Modes](./failure-modes.md).
