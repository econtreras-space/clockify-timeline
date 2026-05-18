# NarrativeInput

Back to [Docs Home](../../README.md), [Architectural Principles](../../blueprint/architectural-principles.md), [Architecture Decisions](../../decisions/README.md), and [Domain Overview](../domain-overview.md).

## Purpose

`NarrativeInput` is the canonical representation of the human update that starts the reconstruction process.

## Canonical Fields/Concepts

- raw update content
- date or reporting context
- timezone when relevant
- minimal surrounding context required to interpret the update

## Invariants

- it is semantic input, not temporal truth
- it may be incomplete, ambiguous, or uneven in detail
- it should preserve the user’s framing before temporal interpretation begins

## Relationships

- `NarrativeInput` is interpreted into [WorkUnit](./work-unit.md) candidates
- it is evaluated against the [Narrative Domain](../narrative-domain.md) rather than provider schemas

## Non-Goals

- it is not a provider payload
- it is not a time allocation
- it is not a proof of what objectively happened
