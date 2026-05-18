# TimelineProposal

Back to [Docs Home](../../README.md), [Architectural Principles](../../blueprint/architectural-principles.md), [Architecture Decisions](../../decisions/README.md), and [Domain Overview](../domain-overview.md).

## Purpose

`TimelineProposal` is the canonical full-day proposal produced by the internal system before provider submission.

## Canonical Fields/Concepts

- collection of reconstructed blocks
- total proposed allocation
- validation or warning signals
- clarification-needed state

## Invariants

- it is reviewable output, not silent system state
- it may carry ambiguity and confidence information
- it must remain subject to user review and confirmation

## Relationships

- `TimelineProposal` is composed of [TimelineBlock](./timeline-block.md) items
- it is the main internal result handed to the [Human Authority Domain](../human-authority-domain.md)
- it can later be translated into [ProviderPayload](./provider-payload.md)

## Non-Goals

- it is not the final provider request
- it is not autonomous approval
- it is not proof of factual activity
