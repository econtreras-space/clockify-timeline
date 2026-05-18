# High-Level Architecture

Back to [Docs Home](../README.md), [Architectural Principles](./architectural-principles.md), [Architecture Decisions](../decisions/README.md), and [Domain Overview](../domain/domain-overview.md).

## Purpose

This page describes the major system areas and their boundaries.

It explains what parts exist, what they own, and how data moves between them at a high level.

## Major Areas

### Inputs and Context

The system begins with external and user-supplied context such as:

- [NarrativeInput](../domain/entities/narrative-input.md)
- calendar context
- user configuration
- workday rules

These inputs do not yet form a provider payload or a final timeline. They form the raw context surface.

### Skill and Orchestration Layer

The orchestration layer coordinates:

- intake,
- context gathering,
- constraint preparation,
- analyzer invocation,
- and user-facing review flow.

It is responsible for sequencing, not for redefining the internal domain.

### Analyzer Core

The analyzer is the reasoning center of the system.

It turns internal domain concepts into a plausible [TimelineProposal](../domain/entities/timeline-proposal.md) through:

- semantic interpretation,
- temporal reconstruction,
- uncertainty handling,
- and clarification-aware safety behavior.

Behavior details live in the [Analyzer Overview](../analyzer/analyzer-overview.md).

### Provider Adapter Layer

The provider adapter layer translates internal results into [ProviderPayload](../domain/entities/provider-payload.md) output.

Its responsibility is serialization, formatting, and downstream submission preparation.

Providers are downstream targets, not domain authorities.

### External Systems

External systems can include:

- Clockify
- calendar systems
- future provider platforms

These systems supply context or receive serialized output, but they do not define the internal model.

## Boundary Rules

- domain concepts are defined in `domain/`
- analyzer behavior is defined in `analyzer/`
- blueprint pages describe system shape and flow
- provider concerns stay at the edge
- user authority remains above autonomous progression

## Architectural Emphasis

The core architectural choice is that the system models semantic work reconstruction and temporal plausibility internally.

External providers exist to receive transformed output, not to shape the internal meaning of work.
