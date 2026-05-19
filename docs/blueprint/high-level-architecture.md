# High-Level Architecture

## Purpose

This page describes the major system areas and their boundaries.

It answers three questions:

- what parts exist
- what each part owns
- where the important handoffs happen

## Major Areas

### Inputs and Context

The system begins with external and user-supplied context such as:

- [NarrativeInput](../domain/entities/narrative-input.md)
- calendar context
- user configuration
- workday rules

These inputs form the reasoning surface. They do not yet form a timeline or a provider payload.

### Orchestration Layer

The orchestration layer coordinates:

- intake,
- context gathering,
- constraint preparation,
- analyzer invocation,
- and user-facing review flow.

It owns sequencing, stage boundaries, and runtime delegation. It does not own domain meaning.

### Analyzer Core

The analyzer turns bounded inputs into a plausible, reviewable [TimelineProposal](../domain/entities/timeline-proposal.md) through:

- semantic interpretation,
- temporal reconstruction,
- uncertainty handling,
- and clarification-aware safety behavior.

Behavior details live in the [Analyzer Overview](../analyzer/analyzer-overview.md).

### Review and Confirmation Gate

Generated output passes through a human review boundary before provider handoff.

This area owns:

- proposal preview
- correction and regeneration
- explicit confirmation before submission

It prevents downstream adapters from becoming the place where acceptability is decided.

### Provider Adapter Layer

The provider adapter layer translates internal results into [ProviderPayload](../domain/entities/provider-payload.md) output.

Its responsibility is serialization, formatting, provider-specific validation, and downstream submission preparation.

### External Systems

External systems can include:

- Clockify
- calendar systems
- future provider platforms

These systems supply context or receive serialized output, but they do not define the internal model.

## Boundary Rules

- domain concepts are defined in `domain/`
- analyzer behavior is defined in `analyzer/`
- blueprint pages describe shape, flow, and ownership boundaries
- provider concerns stay at the edge
- review and confirmation happen before provider submission

## Handoff Summary

- inputs and context prepare the day-level reasoning surface
- orchestration decides when and how stages run
- the analyzer produces a proposal plus confidence signals
- the review gate decides whether the proposal can continue
- provider adapters translate accepted output for external systems
