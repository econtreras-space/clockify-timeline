# Clarification Contract

Back to [Prompt Contracts](./README.md), [Docs Home](../README.md), and [Clarification Loop](../analyzer/clarification-loop.md).

## Purpose

The clarification stage defines when the system must stop and ask for more context instead of continuing with weak reconstruction.

## Allowed To Do

- request missing distinctions
- ask targeted follow-up questions
- trigger regeneration after new context arrives
- direct the user toward correcting ambiguity

## Must Produce

- focused clarification requests
- a clear explanation of what is missing or contradictory
- a path back into proposal generation after the missing context is supplied

## Must Never Do

- ask vague filler questions
- use clarification as cover for hidden fabrication
- bypass validation concerns
- shift all reconstruction work back onto the user by default

## V1 Emphasis

Clarification should be used when the system lacks enough support to produce a believable proposal, not as a decorative conversational step.
