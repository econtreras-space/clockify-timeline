# Glossary

Back to [Docs Home](../README.md), [Architectural Principles](./architectural-principles.md), [Architecture Decisions](../decisions/README.md), and [Domain Overview](../domain/domain-overview.md).

## Purpose

This glossary is a navigation layer.

It helps readers find canonical terms quickly, but it does not replace the `domain/` section as the source of truth.

## Narrative Concepts

- [NarrativeInput](../domain/entities/narrative-input.md): raw human update plus minimal context
- [WorkUnit](../domain/entities/work-unit.md): semantic unit of work extracted from narrative

## Constraint and Temporal Concepts

- [Constraint](../domain/entities/constraint.md): hard boundary or reserved time anchor
- `AvailableGap`: allocatable region after constraints are applied; defined canonically in [Domain Overview](../domain/domain-overview.md)
- [TimelineBlock](../domain/entities/timeline-block.md): reconstructed temporal block
- [TimelineProposal](../domain/entities/timeline-proposal.md): full proposed day allocation
- `Validation/Confidence State`: warnings, ambiguity, and clarification-needed signals; defined canonically in [Domain Overview](../domain/domain-overview.md)

## Provider Concepts

- [ProviderPayload](../domain/entities/provider-payload.md): provider-facing representation derived from internal domain state

## Authority and Review Concepts

- user authority: defined in [Human Authority Domain](../domain/human-authority-domain.md)
- clarification: behavior owned by [Clarification Loop](../analyzer/clarification-loop.md)
- confirmation: authority boundary described in [Human Authority Domain](../domain/human-authority-domain.md)

## Where to Go Next

- For canonical definitions, start in [Domain Overview](../domain/domain-overview.md).
- For subsystem behavior, continue to [Analyzer Overview](../analyzer/analyzer-overview.md).
- For system framing, continue to [System Vision](./system-vision.md) and [High-Level Architecture](./high-level-architecture.md).
