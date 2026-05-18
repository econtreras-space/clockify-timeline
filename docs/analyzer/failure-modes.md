# Failure Modes

Back to [Docs Home](../README.md), [Architectural Principles](../blueprint/architectural-principles.md), [Architecture Decisions](../decisions/README.md), [Domain Overview](../domain/domain-overview.md), and [Analyzer Overview](./analyzer-overview.md).

## Primary Question

How should the analyzer fail safely when it cannot produce a trustworthy reconstruction?

## Role

Failure handling is part of the analyzer design, not an afterthought.

Because the system is interpretive, failure is often about refusing false confidence rather than catching a software crash.

## Failure Classes and Safe Responses

### Poor Narrative Input

When the input is too vague, too short, or too structurally weak to support believable extraction:

- clarify
- warn
- refuse low-confidence proposal if needed

### Impossible Temporal Density

When the described work cannot plausibly fit inside the available day:

- warn
- regenerate with lower density if supported
- clarify where compression assumptions become unsafe

### Calendar Contradiction

When advisory calendar context and reconstructed work collide in a way that weakens plausibility:

- warn
- clarify
- defer to user correction

Calendar data should influence review, not automatically win.

### Excessive Ambiguity

When the system cannot confidently separate tasks, priorities, or likely effort shape:

- clarify
- refuse low-confidence proposal if ambiguity remains unresolved

### Overcompressed Timelines

When the proposal becomes too tight, too robotic, or too continuity-free to feel human:

- regenerate
- reserve more realism through operational noise
- warn if the input still demands implausible packing

### Mismatch With User Expectation

When the generated proposal may be internally coherent but clearly does not match the user’s intent:

- defer to user correction
- regenerate after feedback
- treat the user response as authoritative

## Safety Principle

The analyzer should prefer safe incompleteness over polished nonsense.

That means:

- clarification is better than fabrication
- warning is better than hidden confidence
- refusal is better than false precision

## Related Pages

- [Uncertainty Model](./uncertainty-model.md) explains how ambiguity is represented.
- [Clarification Loop](./clarification-loop.md) explains when the system should ask instead of guessing.
- [Operational Noise](./operational-noise.md) explains one major cause of overcompressed proposals.
