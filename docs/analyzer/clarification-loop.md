# Clarification Loop

## Primary Question

When should the analyzer stop reconstructing and ask for more context instead?

## Role

The clarification loop exists to enforce the principle of clarification over fabrication.

When the analyzer cannot produce a believable proposal from the available context, it should ask targeted follow-up questions instead of forcing a low-quality `TimelineProposal`.

## Common Triggers

Clarification pressure should increase when the analyzer encounters:

- poor narrative quality
- conflicting signals between narrative and constraints
- oversized semantic workload for the available day
- low-confidence allocation support
- unrealistic compression or density

These triggers may come from [Semantic Extraction](./semantic-extraction.md), [Temporal Reconstruction](./temporal-reconstruction.md), or the [Uncertainty Model](./uncertainty-model.md).

## Expected Behavior

The clarification loop should:

- ask targeted follow-up questions
- request missing distinctions rather than generic restatements
- prefer guided correction over a full manual rewrite
- support regeneration after new context arrives

Its purpose is not to interrogate the user. Its purpose is to cheaply recover enough signal for a believable reconstruction.

## Guided Correction

The design intent from the conversation favored constraint-guided correction over dumping the whole burden on the user.

That means the analyzer should prefer prompts like:

- which task likely dominated the afternoon
- whether a meeting-heavy day should compress task work
- whether two described activities should be merged or separated

instead of asking the user to fully rebuild the timeline from scratch.

## Relationship to User Authority

The clarification loop exists because the user remains the final authority.

The system should ask when it does not know enough, then let the user:

- confirm,
- correct,
- refine,
- or reject

the reconstruction path.

## Boundary

This page defines when clarification should happen.

It does not define numeric thresholds or the exact conversational wording of every prompt. Those remain implementation details as long as the architectural behavior is preserved.
