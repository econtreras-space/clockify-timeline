# ADR-005: Calendar Data Is Advisory, Not Authoritative

## Status

Accepted

## Context

Calendar events are useful for shaping the day:

- meetings occupy time,
- schedule anchors reduce allocation freedom,
- and contradictions can reveal impossible proposals.

But calendar events do not fully describe actual work, and they should not override user narrative by default.

## Decision

Calendar data is treated as advisory context and constraint input, not as the authoritative source of what the user did.

It may be used to:

- reserve fixed blocks,
- compute available gaps,
- highlight contradictions,
- and improve plausibility.

It should not be used to:

- infer complete truth about activity,
- dominate the narrative,
- or displace user authority.

## Consequences

- Calendar integration belongs close to constraint-building, not domain ownership.
- The architecture can support calendar-aware reconstruction without becoming calendar-driven.
- Contradictions should trigger review or clarification rather than automatic override.
