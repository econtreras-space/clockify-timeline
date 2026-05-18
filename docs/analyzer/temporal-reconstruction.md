# Temporal Reconstruction

Back to [Docs Home](../README.md), [Architectural Principles](../blueprint/architectural-principles.md), [Architecture Decisions](../decisions/README.md), [Domain Overview](../domain/domain-overview.md), and [Analyzer Overview](./analyzer-overview.md).

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
