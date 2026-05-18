# Calendar Provider

Back to [Docs Home](../README.md), [Architectural Principles](../blueprint/architectural-principles.md), [Architecture Decisions](../decisions/README.md), and [Provider Architecture](./provider-architecture.md).

## Purpose

Calendar systems matter to the architecture, but they play a different role from timesheet submission providers.

They provide advisory context for constraints and plausibility, not the final reporting target.

## Architectural Role

Calendar information can be used to:

- reserve fixed blocks
- expose hard schedule anchors
- reduce allocation freedom
- highlight contradictions that matter during review

This makes calendar systems important to the [Constraint Domain](../domain/constraint-domain.md), not to the ownership of truth.

## Key Invariant

Calendar data is advisory, not authoritative.

It helps shape the day, but it does not automatically overrule:

- the user narrative,
- user correction,
- or human confirmation.

This follows [ADR-005](../decisions/ADR-005-calendar-is-advisory.md).

## What the Calendar Boundary Owns

Calendar-facing integration should own:

- retrieval of event context
- mapping events into constraint-relevant structures
- conflict signaling when proposals overlap fixed anchors

It should not own:

- final approval,
- semantic work interpretation,
- or direct control over final timesheet meaning.

## Relationship to Submission Providers

Calendar systems inform reconstruction.

Clockify-style providers receive final serialized output.

These are different roles and should remain separate in the docs and architecture.
