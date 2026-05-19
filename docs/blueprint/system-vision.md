# System Vision

## Objective

The system exists to reduce the friction of timesheet reporting by transforming human end-of-day narrative updates into plausible, reviewable timeline proposals.

It is designed for people who broadly know what they worked on but do not want to manually reconstruct exact allocations inside tracking software.

## What This Product Is

This is an assisted reconstruction system.

- narrative-to-time translation,
- plausibility-oriented reconstruction,
- and human-in-the-loop reporting support.

## What This Product Is Not

- activity surveillance
- objective productivity measurement
- autonomous truth generation
- automatic timesheet submission

## V1 Focus

V1 focuses on:

- end-of-day narrative input
- hard schedule and calendar-aware constraints
- plausible internal timeline reconstruction
- Clockify-oriented provider output
- explicit human confirmation before submission

## Explicitly Out of Scope for V1

- autonomous reporting without user approval
- activity tracking or monitoring
- multi-day memory continuity as a first-class requirement
- a broader cognition or memory platform

## Product Promise

The system treats narrative as semantic context, not empirical truth.

- It reconstructs plausible proposals rather than claiming to recover exact history.
- It surfaces ambiguity instead of hiding it.
- It leaves final judgment and submission authority with the user.

For system boundaries, continue to [High-Level Architecture](./high-level-architecture.md). For canonical terminology, continue to [Domain Overview](../domain/domain-overview.md).
