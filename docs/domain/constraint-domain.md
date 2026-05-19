# Constraint Domain

## Purpose

The constraint domain defines how the system represents fixed temporal boundaries and reserved time anchors.

It owns the concepts that limit where work can be plausibly allocated during reconstruction.

## Core Concepts

- [Constraint](./entities/constraint.md)
- `AvailableGap`

## Ownership Boundary

This domain is responsible for:

- what counts as a hard boundary,
- how reserved time is represented,
- and how allocatable regions are derived after fixed blocks are removed.

It does not decide what work happened inside those regions. That belongs to the [Temporal Domain](./temporal-domain.md).

## Key Invariants

- hard constraints must be respected
- reserved time anchors shape allocation freedom
- calendar input may inform constraints, but does not become the source of truth

The analyzer uses these concepts during [Temporal Reconstruction](../analyzer/temporal-reconstruction.md).

## AvailableGap

An `AvailableGap` is the remaining allocatable surface after `Constraint` data has been applied.

It is a canonical domain concept even though it does not yet have a dedicated entity page.

## Relationship to Other Domains

The constraint domain supplies the temporal surface that reconstruction operates on.

It also interacts with the [Provider Domain](./provider-domain.md) only indirectly, because provider submission should never redefine what the system considers a valid constraint.
