# Provider Architecture

Back to [Docs Home](../README.md), [Architectural Principles](../blueprint/architectural-principles.md), [Architecture Decisions](../decisions/README.md), and [Provider Domain](../domain/provider-domain.md).

## Purpose

This section explains how external providers fit into the system architecture.

Its focus is not on internal meaning or analyzer behavior. Its focus is on the adapter boundary where internal concepts are translated into provider-facing requests.

## Architectural Role

Providers sit at the system edge.

They consume internal output after the system has already produced and validated a [TimelineProposal](../domain/entities/timeline-proposal.md). Their job is to receive a [ProviderPayload](../domain/entities/provider-payload.md), not to define what work means.

## Interaction Diagram

This diagram focuses on the provider boundary: internal reasoning first, confirmation before handoff, and translation only after the proposal is accepted.

```mermaid
flowchart LR
    subgraph Internal["Internal Domain Output"]
        P["TimelineProposal"]
        V["Validation and Confidence State"]
    end

    subgraph Gate["Review and Confirmation Gate"]
        D["Dry-Run Preview"]
        F["Explicit Confirmation"]
    end

    subgraph Adapters["Provider Adapters"]
        K["Clockify Adapter"]
        G["Calendar Integration"]
        X["Future Provider Adapters"]
    end

    subgraph External["External Systems"]
        CK["Clockify API"]
        GC["Calendar API"]
        FP["Future Provider Systems"]
    end

    P --> D
    V --> D
    D -->|accepted| F
    F --> K
    K -->|ProviderPayload| CK

    G -->|advisory context only| GC
    X -->|ProviderPayload| FP

    classDef edge fill:#f6f8fa,stroke:#9aa4b2,color:#111827;
    classDef review fill:#fff4db,stroke:#d99000,color:#111827;
    classDef provider fill:#e8fff2,stroke:#2c9a62,color:#111827;
    classDef core fill:#e8f1ff,stroke:#4f7cff,color:#111827;

    class CK,GC,FP edge;
    class P,V core;
    class D,F review;
    class K,G,X provider;
```

## What Provider Adapters Own

Provider adapters should own:

- serialization from internal concepts into provider-specific schemas
- authentication and credential use
- submission and retry behavior
- provider-specific validation at the request boundary
- mapping of internal metadata into provider-compatible fields

## What Provider Adapters Do Not Own

Provider adapters should not own:

- semantic interpretation of narrative updates
- timeline plausibility rules
- user authority decisions
- clarification logic
- canonical domain terminology

Those responsibilities stay in the internal domain and analyzer layers.

## Boundary Rule

The most important provider rule is simple:

- internal reasoning happens first
- provider translation happens after

This preserves the provider-agnostic core established in [ADR-002](../decisions/ADR-002-provider-agnostic-domain.md).

## Current and Future Providers

The first concrete target is Clockify.

Calendar systems also matter, but in a different role: they shape constraints and plausibility rather than acting as timesheet submission targets.

Future providers should be added by implementing new adapters, not by changing the internal meaning of:

- [NarrativeInput](../domain/entities/narrative-input.md)
- [WorkUnit](../domain/entities/work-unit.md)
- [Constraint](../domain/entities/constraint.md)
- [TimelineBlock](../domain/entities/timeline-block.md)
- [TimelineProposal](../domain/entities/timeline-proposal.md)

## Related Pages

- [Clockify Adapter](./clockify-adapter.md)
- [Calendar Provider](./calendar-provider.md)
- [Future Provider Strategy](./future-provider-strategy.md)
