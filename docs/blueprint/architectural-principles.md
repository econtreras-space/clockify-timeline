# Architectural Principles

## User Authority

The system proposes, assists, and validates.

It never overrides the user.

The user is the final authority over:

- what was worked on,
- whether the reconstruction is acceptable,
- and whether anything gets submitted.

## Plausibility Over Precision

The system reconstructs plausible timelines from incomplete narrative input.

It does not attempt to:

- discover objective truth,
- measure productivity,
- or prove exact historical activity.

Exactness is an accepted tradeoff in exchange for lower reporting friction.

## Human-in-the-Loop by Default

Generated output must be reviewable before any provider submission.

When the model is uncertain, the system should prefer:

- clarification,
- guided correction,
- or regeneration,

over silent fabrication.

## Provider-Agnostic Core

Clockify is not the core domain.

The internal model should represent:

- narrative work,
- constraints,
- timeline blocks,
- proposals,
- validation state,

without depending on Clockify-specific schemas.

Provider integrations belong in adapters at the edge.

## Calendar as Advisory Context

Calendar data helps build hard constraints and available gaps.

It should not be treated as authoritative proof of actual work performed.

The system may use calendar information to:

- reserve time,
- detect conflicts,
- and shape plausible allocations,

but not to overrule the user narrative.

## Clarification Over Fabrication

Low-confidence inputs should trigger follow-up questions instead of low-quality output.

Examples of situations that should increase clarification pressure:

- vague narratives,
- oversized semantic workload,
- impossible temporal density,
- or unresolved contradictions.

## Operational Noise Is Real

Invisible work is part of real work.

The architecture should allow for operational noise such as:

- coordination overhead,
- context switching,
- fragmentation,
- and slack.

The conversation also suggested reserving a configurable overhead band in future iterations.

## Scope Discipline

V1 remains focused on assisted Clockify timesheet reconstruction.

The architecture can anticipate future memory and continuity systems, but those should not distort the V1 domain model or operating assumptions.
