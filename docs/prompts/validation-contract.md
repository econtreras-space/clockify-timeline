# Validation Contract

Back to [Prompt Contracts](./README.md), [Docs Home](../README.md), and [Analyzer Overview](../analyzer/analyzer-overview.md).

## Purpose

The validation stage decides whether a generated proposal is acceptable, warning-worthy, clarification-worthy, or rejectable before user confirmation and provider handoff.

## Allowed To Do

- inspect proposal coherence
- check constraint consistency
- surface ambiguity and warning signals
- require clarification or regeneration
- block weak output from silently progressing

## Must Produce

- a clear acceptance or rejection state
- warnings where plausibility is weakened but not broken
- clarification-needed signals when context is insufficient
- a reasoned basis for regeneration or refusal

## Must Never Do

- silently approve weak output
- invent missing work to make totals look nicer
- override user authority
- redefine provider payload rules

## Key V1 Rule

Validation must treat invented missing weekdays as invalid behavior, not as a convenience feature.

## Relationship to Other Contracts

- the analyzer proposes
- validation decides whether the proposal may continue
- clarification handles what to ask when validation says the proposal is not strong enough
