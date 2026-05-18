# Proposal Generation

Back to [Prompt Contracts](./README.md), [Docs Home](../README.md), and [Operational Pipeline](../blueprint/operational-pipeline.md).

## Purpose

The proposal generation stage turns validated internal reconstruction output into a reviewable proposal that a user can inspect before provider translation.

## Allowed To Do

- assemble accepted allocations into a coherent proposal
- preserve validation and confidence signals
- present output in a review-friendly structure
- prepare the proposal for confirmation and later provider translation

## Must Produce

- a clear proposal for user review
- preserved warning or clarification metadata
- enough structure for downstream provider translation after confirmation

## Must Never Do

- hide important warnings
- skip the confirmation boundary
- redefine provider-specific output shapes that belong to adapters
- change analyzer meaning after validation

## V1 Emphasis

Proposal generation is downstream from analyzer and validation behavior. It should remain simple until those earlier boundaries are stable.
