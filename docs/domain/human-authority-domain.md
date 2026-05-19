# Human Authority Domain

## Purpose

The human authority domain defines the review and correction boundary around generated proposals.

It exists to ensure that the system remains an assistant rather than an autonomous reporting engine.

## Core Concepts

- user review
- clarification
- correction
- confirmation

## Ownership Boundary

This domain is responsible for:

- how user authority is preserved around generated output,
- when clarification is required,
- and why explicit confirmation matters before submission.

It does not own provider submission behavior itself. It owns the authority boundary that must be satisfied before provider submission becomes permissible.

## Key Invariants

- the user is always the final authority
- low-confidence output should trigger clarification
- confirmation is mandatory before submission
- correction is a first-class behavior, not an exception path

These principles are reflected in:

- [ADR-001](../decisions/ADR-001-user-authority.md)
- [ADR-003](../decisions/ADR-003-human-confirmation-required.md)
- [Clarification Loop](../analyzer/clarification-loop.md)

## Relationship to Other Domains

This domain receives internal output from the [Temporal Domain](./temporal-domain.md) and mediates whether that output is accepted, corrected, or rejected by the user.

It also acts as the safe-response boundary when ambiguity or failure states become too strong for silent progression.
