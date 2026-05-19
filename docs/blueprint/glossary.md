# Glossary

## Purpose

This glossary is a navigation layer for fast skimming.

It helps you find the right page quickly, but it does not replace [Domain Overview](../domain/domain-overview.md) as the source of truth.

## If You Are Trying to Understand the Input Side

- [Narrative Domain](../domain/narrative-domain.md): how user updates enter the system
- [NarrativeInput](../domain/entities/narrative-input.md): the raw reporting input
- [WorkUnit](../domain/entities/work-unit.md): the semantic work extracted from that input

## If You Are Trying to Understand Time Allocation

- [Constraint Domain](../domain/constraint-domain.md): what limits where work can be placed
- [Temporal Domain](../domain/temporal-domain.md): how plausible day structure is represented
- [Temporal Reconstruction](../analyzer/temporal-reconstruction.md): how semantic work becomes time blocks

## If You Are Trying to Understand Review and Safety

- [Human Authority Domain](../domain/human-authority-domain.md): who decides whether the proposal is acceptable
- [Clarification Loop](../analyzer/clarification-loop.md): when the system asks instead of guessing
- [Failure Modes](../analyzer/failure-modes.md): how weak or contradictory cases fail safely

## If You Are Trying to Understand Provider Handoff

- [Provider Domain](../domain/provider-domain.md): the translation boundary from internal meaning to external payloads
- [Provider Architecture](../providers/provider-architecture.md): what adapters own
- [Clockify Adapter](../providers/clockify-adapter.md): the current concrete provider target

## Where to Go Next

- For canonical definitions, start in [Domain Overview](../domain/domain-overview.md).
- For system behavior, continue to [Analyzer Overview](../analyzer/analyzer-overview.md) and [Operational Pipeline](./operational-pipeline.md).
- For the current runtime shape, continue to [Agent-Based Orchestration](./agent-orchestration.md).
