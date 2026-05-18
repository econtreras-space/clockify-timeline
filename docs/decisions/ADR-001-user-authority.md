# ADR-001: User Authority Is Final

## Status

Accepted

## Context

The system generates timeline proposals from incomplete, interpretive narrative input. That makes mistakes, ambiguity, and reconstruction tradeoffs unavoidable.

If the system is allowed to overrule the user, trust collapses and the product shifts from assistant to unsafe automation.

## Decision

The user is always the final authority.

The system may:

- propose timelines,
- ask clarifying questions,
- validate consistency,
- and suggest corrections.

The system may not:

- override user judgment,
- treat its reconstruction as ground truth,
- or submit results as if they were inherently correct.

## Consequences

- The product remains an assistant instead of an autonomous reporter.
- Review and correction flows become first-class parts of the architecture.
- Confidence metadata matters because it informs the user, not because it replaces them.
- Provider submissions must depend on user approval, not model confidence alone.
