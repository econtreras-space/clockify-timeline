# ADR-002: Internal Domain Must Be Provider-Agnostic

## Status

Accepted

## Context

The first concrete target is Clockify, but the problem being solved is broader than any single provider.

If the core model is shaped directly around Clockify payloads, the architecture becomes brittle, harder to reason about, and harder to extend to future providers.

## Decision

The internal domain model must remain independent from provider-specific schemas.

Canonical internal concepts should include domain entities such as:

- narrative input,
- constraints,
- work units,
- timeline blocks,
- timeline proposals,
- and validation state.

Provider-specific concerns belong in adapter layers that translate the internal model into external payloads.

## Consequences

- Clockify stays an integration target, not the source of domain truth.
- Future providers can be added with adapters rather than core rewrites.
- Internal reasoning remains focused on semantic and temporal reconstruction.
- Provider serialization, authentication, and submission logic stay at the system edge.
