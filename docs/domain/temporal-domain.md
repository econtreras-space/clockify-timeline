# Temporal Domain

Back to [Docs Home](../README.md), [Architectural Principles](../blueprint/architectural-principles.md), [Architecture Decisions](../decisions/README.md), and [Domain Overview](./domain-overview.md).

## Purpose

The temporal domain defines how the system represents plausible time structure internally.

It owns the canonical temporal entities used to turn semantic work into reviewable day-level proposals.

## Core Concepts

- `AvailableGap`
- [TimelineBlock](./entities/timeline-block.md)
- [TimelineProposal](./entities/timeline-proposal.md)
- `Validation/Confidence State`

## Ownership Boundary

This domain is responsible for:

- the shape of reconstructed time,
- the internal representation of day-level allocations,
- and the relationship between plausibility, continuity, and reviewability.

It does not own the meaning of narrative input, which belongs to the [Narrative Domain](./narrative-domain.md), and it does not own provider serialization, which belongs to the [Provider Domain](./provider-domain.md).

## Key Invariants

- temporal reconstruction is interpretive, not observational
- proposals must remain human-reviewable
- the system distributes time rather than observing time
- ambiguity and confidence are part of the output, not hidden implementation detail

These behaviors are explained operationally in [Temporal Reconstruction](../analyzer/temporal-reconstruction.md) and [Uncertainty Model](../analyzer/uncertainty-model.md).

## Validation/Confidence State

`Validation/Confidence State` represents warnings, ambiguity, and clarification-needed signals attached to a `TimelineProposal`.

It is a canonical temporal-domain concept even without a standalone page in this pass.

## Relationship to Other Domains

The temporal domain takes semantic meaning from the [Narrative Domain](./narrative-domain.md) and allocatable structure from the [Constraint Domain](./constraint-domain.md).

It then produces internal results that the [Provider Domain](./provider-domain.md) can serialize and the [Human Authority Domain](./human-authority-domain.md) can review.
