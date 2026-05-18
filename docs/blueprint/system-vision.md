# System Vision

Back to [Docs Home](../README.md), [Architectural Principles](./architectural-principles.md), [Architecture Decisions](../decisions/README.md), and [Domain Overview](../domain/domain-overview.md).

## Objective

The system exists to reduce the friction of timesheet reporting by transforming human end-of-day narrative updates into plausible, reviewable timeline proposals.

It is designed for people who broadly know what they worked on but do not want to manually reconstruct exact allocations inside tracking software.

## Product Shape

This is an assisted reconstruction system.

It is not:

- activity surveillance,
- objective productivity measurement,
- or autonomous truth generation.

It is:

- narrative-to-time translation,
- plausibility-oriented reconstruction,
- and human-in-the-loop reporting support.

## V1 Scope

V1 focuses on:

- end-of-day narrative input
- hard schedule and calendar-aware constraints
- plausible internal timeline reconstruction
- Clockify-oriented provider output
- explicit human confirmation before submission

## Core Philosophy

The system treats narrative as semantic context, not empirical truth.

It reconstructs a believable [TimelineProposal](../domain/entities/timeline-proposal.md) from:

- [NarrativeInput](../domain/entities/narrative-input.md),
- [Constraint](../domain/entities/constraint.md),
- `AvailableGap`,
- and uncertainty-aware reasoning.

The user remains the final authority over whether the proposal is acceptable.

## Architectural Direction

The internal model is intentionally provider-agnostic.

That means:

- the internal domain owns meaning,
- the analyzer owns reconstruction behavior,
- and providers remain downstream adapters.

This separation allows the system to stay conceptually stable even as specific integrations evolve.
