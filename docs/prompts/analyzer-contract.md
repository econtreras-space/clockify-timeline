# Analyzer Contract

Back to [Prompt Contracts](./README.md), [Docs Home](../README.md), and [Analyzer Overview](../analyzer/analyzer-overview.md).

## Purpose

The analyzer stage transforms narrative and contextual inputs into a plausible internal proposal without pretending to observe real activity.

## Allowed To Do

- interpret narrative meaning
- derive `WorkUnit` candidates
- allocate plausible time within valid constraint surfaces
- assign an internal `project_key` when the narrative clearly supports one
- surface uncertainty explicitly
- prepare a reviewable proposal for validation
- extract explicit per-project hour budgets from narrative text and treat them as hard allocation targets
- attribute constraint blocks to a project when the schedule config specifies `project_key` on that constraint entry
- report shortfall between user-stated total and configured daily target without expanding blocks to fill it

## Must Produce

- a proposal-level internal structure
- temporal allocations that respect constraints
- optional provider-agnostic project assignment per relevant block
- ambiguity and confidence signals
- enough traceability for validation and review to operate

## Must Never Do

- invent entire missing workdays
- fabricate work that is absent from the usable narrative context
- treat fixed schedule defaults as permanent architecture
- bypass clarification when support is too weak
- shape internal meaning around Clockify-specific fields
- force every day to fill the configured target surface when the narrative only supports a shorter day
- expand block durations beyond the user-stated budget to reach `productive_hours_per_day`
- discard constraint hours from a project's budget when the constraint is attributed to that project via `project_key`

## Key V1 Rule

The analyzer may allocate time across a described day or across described work within the valid reporting window, but it must not reconstruct unreported weekdays as if they were known. Shorter valid days are allowed when the narrative support is partial.

## Relationship to Other Contracts

- validation decides whether analyzer output is strong enough
- clarification recovers missing context when analyzer support is insufficient
- proposal generation packages validated analyzer output into a reviewable form
