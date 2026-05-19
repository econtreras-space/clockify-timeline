# Prompt Contracts

Back to [Docs Home](../README.md), [Architectural Principles](../blueprint/architectural-principles.md), [Architecture Decisions](../decisions/README.md), and [V1 Validation Checklist](../v1-validation-checklist.md).

## Purpose

This folder exists to document prompt behavior as contracts.

It is not intended to become a dump of long prompt text fragments. Its purpose is to define what each prompt-driven stage is responsible for, what it must output, and what it must never do.

## Why This Folder Exists

As the wiki grows, architecture alone is not enough to keep a live skill coherent.

The contracts in this folder are the bridge between:

- the domain model,
- the analyzer behavior,
- the validation boundary,
- and the actual skill implementation.

## Prompt Authoring Order

The recommended V1 authoring order is:

1. [Validation Contract](./validation-contract.md)
2. [Analyzer Contract](./analyzer-contract.md)
3. [Clarification Contract](./clarification-contract.md)
4. [Proposal Generation](./proposal-generation.md)

This order is intentional. Validation and analyzer boundaries should be clear before the system spends more effort on prompt elaboration.

## Contract Rule

Every prompt contract should answer three things clearly:

- what this stage is allowed to do
- what this stage must produce
- what this stage must never do

If a prompt doc does not improve one of those three boundaries, it is probably not a contract yet.
