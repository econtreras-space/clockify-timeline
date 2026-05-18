# ADR-003: Human Confirmation Is Required Before Submission

## Status

Accepted

## Context

The system is intentionally interpretive. It reconstructs a plausible allocation, not an objective recording of activity.

Because of that, silent submission would create unnecessary risk:

- wrong allocations,
- false confidence,
- and loss of user trust.

## Decision

Every generated proposal must pass through an explicit confirmation loop before provider submission.

The minimum flow is:

1. Generate a dry-run proposal.
2. Present it in a human-reviewable format.
3. Allow correction, clarification, regeneration, or rejection.
4. Submit only after explicit approval.

## Consequences

- A preview state becomes part of the product, not just the UX.
- Regeneration and correction are expected behaviors, not exception paths.
- The system can be helpful without pretending to be authoritative.
- Full automation is intentionally constrained in V1.
