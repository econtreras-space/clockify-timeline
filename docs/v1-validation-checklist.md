# V1 Validation Checklist

Back to [Docs Home](./README.md), [Architectural Principles](./blueprint/architectural-principles.md), [Architecture Decisions](./decisions/README.md), and [Prompt Contracts](./prompts/README.md).

## Purpose

This checklist defines the recommended implementation order for reaching a real V1 quickly while preserving the architecture already documented in this wiki.

It is optimized for early validation, not long-term polish.

## Guiding Corrections

The current implementation direction must respect three explicit constraints:

- the system must not recreate missing workdays with invented context-based tasks
- fixed daily schedule defaults are temporary and should move into configurable rules
- final provider-facing payloads should stay provider-aligned and owned by the adapter boundary rather than redefined in core docs

## Recommended Order

### 1. Lock the Real V1 Rules

Before refining prompts or scripts further, freeze the actual V1 rules that the system is allowed to enforce.

The first rule set should make the following explicit:

- no invented missing weekdays
- no fabricated work that is absent from the narrative
- schedule assumptions are defaults, not permanent architecture
- user confirmation is mandatory before provider handoff

This step matters because undocumented “helpful defaults” are currently the fastest path to domain drift.

### 2. Define the Minimal Internal Contracts

Before adding detailed prompt contracts, make sure the internal shapes are stable enough to support the pipeline.

The minimum set to stabilize is:

- parsed narrative result
- normalized `WorkUnit` output
- proposal-level structure before provider translation
- validation result shape

These do not replace provider-aligned payloads. They protect the internal system from being shaped by provider formats too early.

### 3. Write the Validation Contract First

The first prompt-side contract to formalize should be [Validation Contract](./prompts/validation-contract.md).

This should define:

- what must always be true before a proposal can move forward
- what conditions produce warnings
- what conditions require clarification
- what conditions force refusal or regeneration

This is the fastest way to prevent weak output from looking “good enough” too early.

### 4. Write the Analyzer Contract Second

Once validation behavior is clear, formalize [Analyzer Contract](./prompts/analyzer-contract.md).

This should define:

- what the analyzer is allowed to infer
- what it must not invent
- what inputs it requires
- what outputs it must produce
- how ambiguity should surface into downstream validation

This turns the analyzer from a fuzzy prompt into a bounded subsystem.

### 5. Separate the Real Pipeline Stages in the Skill

Even if the implementation stays in one skill file at first, the operating stages should be made explicit:

- parse
- reconstruct
- validate
- confirm
- push

If these remain blended together, the wiki can keep improving while the implementation stays operationally ambiguous.

### 6. Write the Clarification Contract Third

After validation and analyzer responsibilities are bounded, formalize [Clarification Contract](./prompts/clarification-contract.md).

This should define:

- when the system must stop and ask
- what kinds of follow-up questions are acceptable
- how clarification differs from fabrication
- how regeneration should be triggered after new context arrives

### 7. Write the Proposal Generation Contract Fourth

The last of the initial prompt contracts should be [Proposal Generation](./prompts/proposal-generation.md).

This should describe how validated internal structures become a reviewable proposal before provider translation.

It belongs later because it depends on the earlier contracts being stable.

## What to Avoid During V1

- Do not make provider payloads the center of the system.
- Do not let the skill invent full missing days to satisfy a weekly target.
- Do not treat fixed schedule assumptions as architecture.
- Do not add large prompt prose before the validation boundary is clear.
- Do not optimize for polished automation before testing correction and confirmation loops.

## Minimal Success Criteria for V1

V1 is successful if the system can:

- accept real narrative input
- reconstruct only from described or defensible context
- apply configurable schedule rules
- produce a reviewable proposal
- reject or clarify weak cases
- require explicit confirmation
- hand off accepted output to the Clockify adapter cleanly

## Suggested Execution Sequence

If you want a strict “do this next” order:

1. stabilize V1 rules
2. stabilize internal contracts
3. implement validation contract
4. implement analyzer contract
5. refactor the skill into explicit stages
6. implement clarification contract
7. implement proposal generation contract
8. validate the end-to-end flow with real samples
