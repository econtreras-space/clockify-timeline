# Analyzer Contract

Back to [Prompt Contracts](./README.md), [Docs Home](../README.md), and [Analyzer Overview](../analyzer/analyzer-overview.md).

## Purpose

The analyzer stage transforms narrative and contextual inputs into a plausible internal proposal without pretending to observe real activity.

## Allowed To Do

- interpret narrative meaning
- derive `WorkUnit` candidates
- allocate plausible time within valid constraint surfaces
- surface uncertainty explicitly
- prepare a reviewable proposal for validation

## Must Produce

- a proposal-level internal structure
- temporal allocations that respect constraints
- ambiguity and confidence signals
- enough traceability for validation and review to operate

## Must Never Do

- invent entire missing workdays
- fabricate work that is absent from the usable narrative context
- treat fixed schedule defaults as permanent architecture
- bypass clarification when support is too weak
- shape internal meaning around Clockify-specific fields

## Key V1 Rule

The analyzer may allocate time across a described day or across described work within the valid reporting window, but it must not reconstruct unreported weekdays as if they were known.

## Relationship to Other Contracts

- validation decides whether analyzer output is strong enough
- clarification recovers missing context when analyzer support is insufficient
- proposal generation packages validated analyzer output into a reviewable form
