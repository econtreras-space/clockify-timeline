# Semantic Extraction

Back to [Docs Home](../README.md), [Architectural Principles](../blueprint/architectural-principles.md), [Architecture Decisions](../decisions/README.md), [Domain Overview](../domain/domain-overview.md), and [Analyzer Overview](./analyzer-overview.md).

## Primary Question

How does the analyzer turn a `NarrativeInput` into `WorkUnit` structures before any temporal allocation happens?

## Role

Semantic extraction is the phase that interprets meaning without yet assigning hours or clock times.

Its responsibility is to identify what kinds of work the user is describing, how those pieces relate to each other, and where the narrative is too vague to support confident reconstruction.

## Inputs

Semantic extraction starts from:

- the raw `NarrativeInput`,
- minimal context such as date or role expectations when available,
- and any obvious narrative structure already present in the user update.

It does not require provider payloads, exact historical events, or final time gaps to do its job.

## Responsibilities

This phase should cover the following concerns:

- parse bullet points, sentences, or mixed-format updates into a normalized structure
- identify candidate `WorkUnit` entries
- separate independent work from supporting or related work where possible
- estimate relative semantic importance or cognitive weight
- detect vague, overloaded, or underspecified language

## What a WorkUnit Is

A `WorkUnit` is a semantic unit of work, not a temporal allocation.

It can represent:

- a coding task,
- a debugging effort,
- a review pass,
- a research thread,
- an architecture discussion,
- or a coordination-heavy activity.

The purpose of a `WorkUnit` is to preserve meaning before time gets distributed.

## Important Invariant

Semantic importance is not equal to time spent.

A narratively important task may have taken little time, and a lightly described task may have consumed a large part of the day. This is why semantic extraction must stay separate from [Temporal Reconstruction](./temporal-reconstruction.md).

## Example

Narrative:

`Implemented sync layer, reviewed two PRs, and handled a short production issue.`

Possible `WorkUnit` interpretation:

- sync layer implementation
- PR review
- production issue response

This phase should stop there. It should not yet decide whether one task took 30 minutes or three hours.

## Ambiguity Detection

Semantic extraction is also the first place where uncertainty becomes visible.

Common ambiguity patterns include:

- very broad verbs such as "worked on" or "fixed stuff"
- bundled tasks with unclear boundaries
- updates that imply more work than a normal day can plausibly hold
- statements that describe importance but not shape

These signals should be handed forward into the [Uncertainty Model](./uncertainty-model.md), not silently ignored.

## Hand-off

The output of semantic extraction is a set of `WorkUnit` candidates plus ambiguity markers that later phases can use during:

- temporal allocation,
- confidence scoring,
- and clarification decisions.
