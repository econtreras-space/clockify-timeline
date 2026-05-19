# Constraint

## Purpose

`Constraint` is the canonical representation of a hard temporal boundary or reserved time anchor.

## Canonical Fields/Concepts

- constraint type
- start and end boundary when applicable
- reserved or fixed nature
- origin, such as schedule rule or calendar anchor

## Invariants

- constraints bound allocation freedom
- hard constraints must be respected
- advisory data may help form a constraint, but does not become the source of truth by itself

## Relationships

- `Constraint` shapes `AvailableGap`
- `Constraint` bounds where [TimelineBlock](./timeline-block.md) allocations can appear
- it belongs to the [Constraint Domain](../constraint-domain.md)

## Non-Goals

- it is not a work description
- it is not a user approval signal
- it is not a provider-specific scheduling schema
