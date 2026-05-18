# Operational Noise

Back to [Docs Home](../README.md), [Architectural Principles](../blueprint/architectural-principles.md), [Architecture Decisions](../decisions/README.md), [Domain Overview](../domain/domain-overview.md), and [Analyzer Overview](./analyzer-overview.md).

## Primary Question

How does the analyzer account for real work that is hard to narrate as clean deliverable blocks?

## Role

Operational noise is the realism-preserving allowance for invisible labor and fragmentation that exists in normal workdays.

It helps the analyzer avoid producing schedules that are technically full but behaviorally unrealistic.

## What Counts as Operational Noise

Operational noise can include:

- coordination overhead
- context switching
- communication friction
- waiting, handoff, or follow-up time
- slack required for a human day to remain believable

This is especially important in roles where maintaining system order, enabling others, or handling interruptions consumes real effort without always producing a discrete artifact.

## Important Invariant

Operational noise is not fake time.

It is a modeling concept that acknowledges that not all legitimate work appears as a crisp deliverable or a narratively prominent `WorkUnit`.

Without it, the analyzer tends to overpack the day and drift toward robotic reconstruction.

## Architectural Use

Operational noise should influence [Temporal Reconstruction](./temporal-reconstruction.md) by reducing unrealistic density and preserving room for normal human workflow behavior.

It should also influence [Failure Modes](./failure-modes.md), because proposals that ignore invisible work can look coherent on paper while still feeling obviously wrong to users.

## V1 and Future Direction

The conversation established that V1 should support the concept even if it does not fully expose deep configuration yet.

Future versions may make this more configurable across roles or profiles, but the architecture should already treat it as a real factor rather than an optional embellishment.

## Qualitative Range

The documentation intentionally avoids locking exact percentages or thresholds.

Still, the design assumption is that some roles will naturally carry more operational noise than others. That should remain a future-tunable policy choice, not a hidden architectural surprise.
