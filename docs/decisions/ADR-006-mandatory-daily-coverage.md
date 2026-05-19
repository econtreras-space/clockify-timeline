# ADR-006: Productive Hours Are Guidance, Not Mandatory Coverage

## Status

Superseded by the current agent-oriented V1 direction

## Context

An earlier direction treated `productive_hours_per_day` as mandatory coverage and required the analyzer to fill every day's available surface.

That position conflicts with the current V1 boundary:

- the system may allocate time only within described or defensibly implied work
- schedule defaults are configurable guidance, not permanent architecture
- shorter valid days must remain possible when the narrative support is partial

## Decision

`productive_hours_per_day` should be treated as a configurable target surface or ceiling, not as a mandatory fill requirement.

After the initial temporal distribution of narrative work units into blocks, the system may proportionally expand already-described work when that remains plausible within the same workday. Expansion is allowed, but not required.

Validation may warn when a day appears partial, but it must not assume the narrative supports full-day coverage if that support is absent.

## Consequences

- Proposals may still use bounded expansion when the narrative support is strong.
- Shorter valid days remain representable without forcing hidden fabrication-by-expansion.
- Validation should treat low-hour days as warning-worthy or clarification-worthy based on confidence, not as automatic policy failures.
- User review remains the final authority over whether a partial proposal is acceptable for submission.
