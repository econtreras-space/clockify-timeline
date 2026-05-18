# ADR-004: Plausibility Is Preferred Over Precision

## Status

Accepted

## Context

The product goal is to reduce reporting friction for people who broadly know what they worked on but do not want to reconstruct exact time allocations manually.

The conversation explicitly rejected architectures that depend on universal, empirical activity tracking as a prerequisite for usefulness.

## Decision

The system should optimize for plausible, human-acceptable reconstruction rather than exact historical precision.

This means:

- narrative input is semantic context, not temporal truth,
- semantic importance is not automatically equal to time spent,
- and the analyzer distributes time rather than observing time.

## Consequences

- Confidence, ambiguity, and clarification must be modeled explicitly.
- The system can work from imperfect end-of-day summaries.
- Exactness is treated as a cost, not the primary success metric.
- The output is designed to be believable and reviewable, not provably factual.
