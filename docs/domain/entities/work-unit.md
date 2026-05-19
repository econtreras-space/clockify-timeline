# WorkUnit

## Purpose

`WorkUnit` is the canonical semantic unit of work extracted from `NarrativeInput`.

## Canonical Fields/Concepts

- work description
- category or type of activity when discernible
- relative semantic importance or cognitive weight
- ambiguity markers when the unit is underspecified

## Invariants

- it is semantic, not temporal
- its importance does not automatically equal time spent
- it exists before timeline allocation begins

## Relationships

- `WorkUnit` is derived from [NarrativeInput](./narrative-input.md)
- `WorkUnit` is later mapped into [TimelineBlock](./timeline-block.md) structures
- ambiguity around `WorkUnit` quality contributes to `Validation/Confidence State`

## Non-Goals

- it is not a clock-time block
- it is not a provider-formatted item
- it is not a guarantee of exact effort duration
