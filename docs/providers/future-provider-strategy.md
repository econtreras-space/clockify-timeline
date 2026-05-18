# Future Provider Strategy

Back to [Docs Home](../README.md), [Architectural Principles](../blueprint/architectural-principles.md), [Architecture Decisions](../decisions/README.md), and [Provider Architecture](./provider-architecture.md).

## Purpose

This page defines how new providers should be added without disturbing the core system model.

## Strategy

New providers should be introduced by adding new adapters that consume existing internal concepts.

The preferred extension path is:

1. keep the internal domain unchanged
2. reuse the same accepted [TimelineProposal](../domain/entities/timeline-proposal.md) shape
3. introduce provider-specific serialization at the edge
4. keep provider-specific validation local to the adapter

## Adapter Contract

A new provider integration should be expected to answer these questions:

- what payload shape does the provider require
- what metadata mapping is needed
- what authentication model is required
- what submission or retry behavior belongs at the edge
- what provider-specific errors must be surfaced back to the system

It should not require the internal domain to adopt provider-native terminology just to make the adapter easier to implement.

## Safe Growth Rule

If adding a new provider requires redefining:

- [WorkUnit](../domain/entities/work-unit.md)
- [Constraint](../domain/entities/constraint.md)
- [TimelineBlock](../domain/entities/timeline-block.md)
- [TimelineProposal](../domain/entities/timeline-proposal.md)

then the architecture is probably leaking provider concerns into the core.

## Examples

Likely future providers could include:

- Harvest
- Tempo
- internal enterprise reporting systems

The important point is not which provider comes next. The important point is that each new provider should arrive through the same adapter boundary rather than through a domain rewrite.
