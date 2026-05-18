# Domain Overview

Back to [Docs Home](../README.md), [Architectural Principles](../blueprint/architectural-principles.md), and [Architecture Decisions](../decisions/README.md).

## Purpose

This section is the canonical source of domain terminology for the system.

It defines the internal concepts that appear across:

- the analyzer,
- the blueprint pages,
- and future implementation discussions.

The domain layer owns definitions. Other sections should reference these concepts instead of creating parallel glossaries.

## Domain Areas

The internal model is organized around five major areas:

- [Narrative Domain](./narrative-domain.md): how human updates enter the system as meaningful input
- [Constraint Domain](./constraint-domain.md): how hard boundaries and reserved time shape the day
- [Temporal Domain](./temporal-domain.md): how the system represents plausible time structure
- [Provider Domain](./provider-domain.md): how internal concepts are translated outward without shaping the core model
- [Human Authority Domain](./human-authority-domain.md): how review, correction, and confirmation remain first-class

## Canonical Concepts

The following terms should be used consistently across the docs set:

- [NarrativeInput](./entities/narrative-input.md): raw human update plus minimal context
- [WorkUnit](./entities/work-unit.md): semantic unit of work extracted from narrative
- [Constraint](./entities/constraint.md): hard boundary or reserved time anchor
- `AvailableGap`: allocatable region after constraints are applied
- [TimelineBlock](./entities/timeline-block.md): reconstructed temporal block
- [TimelineProposal](./entities/timeline-proposal.md): full proposed day allocation
- [ProviderPayload](./entities/provider-payload.md): provider-facing representation derived from internal domain state
- `Validation/Confidence State`: warnings, ambiguity, and clarification-needed signals attached to a proposal

`AvailableGap` and `Validation/Confidence State` are canonical concepts even though they do not have standalone entity pages in this pass.

## How the Areas Relate

The system starts with narrative interpretation, where a [NarrativeInput](./entities/narrative-input.md) becomes one or more [WorkUnit](./entities/work-unit.md) candidates.

That semantic meaning is then bounded by the [Constraint Domain](./constraint-domain.md), which determines what parts of the day are fixed and what parts remain available for allocation.

The [Temporal Domain](./temporal-domain.md) uses those concepts to produce [TimelineBlock](./entities/timeline-block.md) structures and a [TimelineProposal](./entities/timeline-proposal.md).

The [Provider Domain](./provider-domain.md) then translates the internal proposal into a [ProviderPayload](./entities/provider-payload.md) without redefining the domain itself.

The [Human Authority Domain](./human-authority-domain.md) governs review, correction, and confirmation around the proposal.

## Relationship to Behavior

This section defines concepts, not subsystem behavior.

Behavioral details live primarily in the analyzer pages, especially:

- [Analyzer Overview](../analyzer/analyzer-overview.md)
- [Semantic Extraction](../analyzer/semantic-extraction.md)
- [Temporal Reconstruction](../analyzer/temporal-reconstruction.md)
- [Uncertainty Model](../analyzer/uncertainty-model.md)

Those pages should use the terms defined here rather than redefining them.
