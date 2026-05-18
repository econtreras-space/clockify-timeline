# ProviderPayload

Back to [Docs Home](../../README.md), [Architectural Principles](../../blueprint/architectural-principles.md), [Architecture Decisions](../../decisions/README.md), and [Domain Overview](../domain-overview.md).

## Purpose

`ProviderPayload` is the canonical provider-facing representation derived from internal domain state.

## Canonical Fields/Concepts

- target provider type
- serialized entry structures
- provider-specific metadata
- formatting or submission-ready shape

## Invariants

- it is downstream from internal reasoning
- it must not redefine the core domain
- it exists at the adapter boundary, not the center of the model

## Relationships

- `ProviderPayload` is derived from [TimelineProposal](./timeline-proposal.md)
- it belongs to the [Provider Domain](../provider-domain.md)
- it supports provider submission without becoming the source of domain truth

## Non-Goals

- it is not a canonical internal timeline concept
- it is not the source of work meaning
- it is not allowed to shape core domain definitions backward
