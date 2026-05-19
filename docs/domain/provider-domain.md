# Provider Domain

## Purpose

The provider domain defines how internal concepts are translated into external system payloads without allowing those external schemas to shape the core model.

It exists to preserve provider-agnostic architecture.

## Core Concepts

- [ProviderPayload](./entities/provider-payload.md)
- provider adapter boundary

## Ownership Boundary

This domain is responsible for:

- translation from internal concepts into provider-facing representations,
- downstream formatting and serialization concerns,
- and keeping provider schemas at the system edge.

It is not responsible for defining what work means, what a day looks like, or whether a proposal is acceptable. Those responsibilities remain inside the internal domain.

## Key Invariants

- providers are adapters, not domain authorities
- provider schemas must not define canonical internal concepts
- serialization happens after internal reasoning, not during it

These principles are grounded in [ADR-002](../decisions/ADR-002-provider-agnostic-domain.md).

## Relationship to Other Domains

The provider domain receives internal structures such as [TimelineProposal](./entities/timeline-proposal.md) and turns them into [ProviderPayload](./entities/provider-payload.md) output.

It depends on the internal domain for meaning, but the internal domain must not depend on provider-specific shapes in return.
