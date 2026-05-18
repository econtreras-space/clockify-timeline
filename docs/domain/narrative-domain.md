# Narrative Domain

Back to [Docs Home](../README.md), [Architectural Principles](../blueprint/architectural-principles.md), [Architecture Decisions](../decisions/README.md), and [Domain Overview](./domain-overview.md).

## Purpose

The narrative domain defines how human work descriptions enter the system as meaningful internal input.

It owns the idea that the system begins with narrative context, not direct temporal truth.

## Core Concepts

- [NarrativeInput](./entities/narrative-input.md)
- [WorkUnit](./entities/work-unit.md)

## Ownership Boundary

This domain is responsible for:

- what the system receives from the user,
- how that input is treated as semantic context,
- and why the narrative is interpreted before any temporal allocation happens.

It is not responsible for assigning clock time. That hand-off belongs to the [Temporal Domain](./temporal-domain.md).

## Key Invariants

- narrative is not temporal truth
- a user update is interpretive input, not empirical tracking data
- semantic importance is not automatically equal to time spent

These invariants are operationalized in [Semantic Extraction](../analyzer/semantic-extraction.md).

## Relationship to Other Domains

The narrative domain hands semantic meaning forward into the temporal model through `WorkUnit` structures.

It also shapes the [Human Authority Domain](./human-authority-domain.md), because the user remains the ultimate source of context when the narrative is incomplete or ambiguous.
