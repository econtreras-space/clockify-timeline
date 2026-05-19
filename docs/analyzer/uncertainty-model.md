# Uncertainty Model

## Primary Question

How does the analyzer represent ambiguity and confidence without pretending to know more than it does?

## Role

Uncertainty is a first-class analyzer concern.

The system operates on incomplete human narrative, partial context, and interpretive temporal reasoning. That means uncertainty is not an edge case. It is part of the normal operating model.

## Sources of Uncertainty

The analyzer should expect ambiguity from several directions:

- vague narrative wording
- underspecified task boundaries
- overloaded or unrealistic days
- contradiction between narrative and calendar or constraint context
- insufficient allocation surface after constraints are applied

Some uncertainty starts in [Semantic Extraction](./semantic-extraction.md). Some emerges only during [Temporal Reconstruction](./temporal-reconstruction.md).

## What the Model Should Produce

The uncertainty model should surface its conclusions through explicit outputs:

- confidence metadata
- warnings
- clarification-needed signals
- refusal to overconfidently reconstruct weak inputs

These belong inside or alongside the `Validation/Confidence State` rather than being hidden inside internal reasoning.

## What Confidence Means

Confidence should be interpreted as support for plausibility, not proof of truth.

High confidence means:

- the narrative is sufficiently structured,
- the reconstructed day is internally coherent,
- and the allocation feels believable under the known constraints.

Low confidence means the analyzer should become more cautious, not more creative.

## Design Boundaries

The docs do not freeze numeric thresholds, scoring bands, or exact weighting formulas.

Those are future implementation details.

What matters at the architecture level is that:

- uncertainty is visible,
- ambiguity changes behavior,
- and confidence affects whether the system proposes, warns, or asks for clarification.

## Relationship to Other Pages

- [Clarification Loop](./clarification-loop.md) owns the behavior when uncertainty becomes actionably high.
- [Failure Modes](./failure-modes.md) owns the safe-response catalog when uncertainty creates unusable output.
- [Operational Noise](./operational-noise.md) explains one realism factor that can reduce false precision.
