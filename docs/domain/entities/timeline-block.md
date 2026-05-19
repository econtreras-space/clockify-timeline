# TimelineBlock

## Purpose

`TimelineBlock` is the canonical reconstructed temporal block produced during allocation.

## Canonical Fields/Concepts

- start and end time
- duration
- associated work meaning
- confidence or traceability metadata when relevant

## Invariants

- it is reconstructed, not observed
- it must fit within the available temporal surface
- it must remain reviewable by a human

## Relationships

- `TimelineBlock` is shaped by [WorkUnit](./work-unit.md), `Constraint`, and `AvailableGap`
- multiple `TimelineBlock` items compose a [TimelineProposal](./timeline-proposal.md)
- ambiguity around block plausibility feeds `Validation/Confidence State`

## Non-Goals

- it is not a guarantee of exact historical timing
- it is not a provider payload on its own
- it does not override user correction
