# AI-Assisted Timesheet Reconstruction Docs

This folder captures the architectural decisions for the Clockify-oriented timesheet reconstruction system discussed in the shared conversation:

- semantic narrative in,
- plausible timeline proposal out,
- explicit human review before submission.

## What matters most

- The system optimizes for plausibility, not factual reconstruction.
- The user is always the final authority.
- The internal domain must stay independent from any single provider.
- Clockify is an adapter target, not the core model.
- Calendar context is advisory and constraint-building input, not truth.

## High-Level Architecture

This diagram is intentionally interaction-focused. It shows how information moves through the system without re-explaining every domain concept visually.

```mermaid
flowchart LR
    subgraph Inputs["External Inputs and Context"]
        N["EOD Narrative"]
        C["Calendar Context"]
        U["User Config"]
    end

    subgraph Skill["Skill and Orchestration"]
        I["Input Intake"]
        B["Constraint Builder"]
        O["Flow Orchestration"]
    end

    subgraph Core["Internal Core"]
        A["Analyzer Engine"]
        P["Timeline Proposal"]
        V["Validation and Confidence Signals"]
    end

    subgraph Review["Human Review Loop"]
        D["Dry-Run Preview"]
        R["User Review and Corrections"]
        F["Explicit Confirmation"]
    end

    subgraph Providers["Provider Adapters"]
        K["Clockify Adapter"]
        G["Calendar Integration"]
        X["Future Provider Adapters"]
    end

    subgraph External["External Systems"]
        CK["Clockify API"]
        GC["Calendar API"]
        FP["Future Provider Systems"]
    end

    N --> I
    C --> G
    U --> I
    U --> B
    G --> B
    I --> O
    B --> O
    O --> A
    A --> P
    A --> V
    P --> D
    V --> D
    D --> R
    R -->|clarify or regenerate| O
    R -->|accept| F
    F --> K
    K --> CK
    X --> FP

    classDef edge fill:#f6f8fa,stroke:#9aa4b2,color:#111827;
    classDef core fill:#e8f1ff,stroke:#4f7cff,color:#111827;
    classDef review fill:#fff4db,stroke:#d99000,color:#111827;
    classDef provider fill:#e8fff2,stroke:#2c9a62,color:#111827;

    class N,C,U,CK,GC,FP edge;
    class I,B,O,A,P,V core;
    class D,R,F review;
    class K,G,X provider;
```

## Start Here

- [Architectural Principles](./blueprint/architectural-principles.md)
- [Architecture Decisions](./decisions/README.md)
- [Domain Overview](./domain/domain-overview.md)
- [Analyzer Overview](./analyzer/analyzer-overview.md)
- [System Vision](./blueprint/system-vision.md)
- [High-Level Architecture](./blueprint/high-level-architecture.md)
- [Operational Pipeline](./blueprint/operational-pipeline.md)
- [Glossary](./blueprint/glossary.md)
- [Provider Architecture](./providers/provider-architecture.md)
- [V1 Validation Checklist](./v1-validation-checklist.md)
- [Prompt Contracts](./prompts/README.md)

## Current V1 Scope

- End-of-day narrative input
- Fixed schedule and calendar-aware constraints
- Plausible timeline reconstruction
- Clockify-compatible output
- Mandatory confirmation loop

## Explicitly Out of Scope for V1

- Autonomous timesheet submission without user approval
- Activity tracking or surveillance
- Multi-day memory continuity as a first-class requirement
- A broader cognition or memory platform
