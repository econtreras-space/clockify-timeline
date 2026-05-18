# Clockify Adapter

Back to [Docs Home](../README.md), [Architectural Principles](../blueprint/architectural-principles.md), [Architecture Decisions](../decisions/README.md), and [Provider Architecture](./provider-architecture.md).

## Purpose

The Clockify adapter is the concrete provider adapter for the current V1 target.

Its role is to translate an accepted internal [TimelineProposal](../domain/entities/timeline-proposal.md) into Clockify-compatible requests without allowing Clockify’s schema to reshape the internal model.

## What It Owns

The Clockify adapter should own:

- transformation of internal timeline structures into Clockify entry payloads
- provider-specific field mapping such as workspace, project, tag, or billable metadata
- authentication concerns
- request formatting and submission behavior
- handling of Clockify-specific validation or request errors

## What It Must Not Own

The Clockify adapter must not own:

- what a `WorkUnit` means
- whether a proposed day is plausible
- whether the user has confirmed the result
- the canonical structure of `TimelineBlock` or `TimelineProposal`

Those decisions belong upstream.

## Input and Output Boundary

The adapter takes internal output after:

- semantic interpretation,
- temporal reconstruction,
- uncertainty handling,
- and human confirmation

have already occurred.

It produces a Clockify-shaped [ProviderPayload](../domain/entities/provider-payload.md) suitable for downstream submission.

## V1 Position

Clockify is the first concrete target, but it is still only a target.

The architecture should treat it as:

- important for delivery,
- specific in its request format,
- but non-authoritative with respect to core domain meaning.

## Why This Matters

If Clockify fields were allowed to shape the internal model directly, future provider support would become harder and internal reasoning would become less coherent.

The adapter boundary protects against that drift.

---

## V1 Payload Schema

The JSON file written to `/tmp/clockify_entries.json` before calling `push_clockify.py` or `generate_timesheet.py` must match this exact top-level shape. Both scripts read `data["entries"]` directly — nested structures will cause a `KeyError`.

```json
{
  "entries": [
    {
      "date":        "YYYY-MM-DD",
      "start":       "HH:MM",
      "end":         "HH:MM",
      "description": "Block description",
      "hours":       1.5,
      "project_id":  "clockify-project-id-or-null"
    }
  ]
}
```

`project_id` is provider-facing. It is derived at the adapter boundary from an internal block `project_key` and may be `null` for projectless entries.

Rules enforced by `push_clockify.py`:
- Entries with `description` equal to `"lunch break"` (case-insensitive) are silently skipped.
- Entries with `hours` ≤ 0 are silently skipped.
- If an entry includes `"project_id": null`, it is pushed without a Clockify project.
- If an entry omits `project_id`, the push script may fall back to the credentials-level default project for backwards compatibility.
- All other entries are submitted in order, 300ms apart.

`generate_timesheet.py` additionally reads an optional top-level `"summary"` key:

```json
{
  "entries": [...],
  "summary": {
    "total_days":   1,
    "total_hours":  8.0,
    "date_range":   "YYYY-MM-DD to YYYY-MM-DD"
  }
}
```

`summary` is optional — the XLSX generator falls back gracefully when it is absent.
When present, `summary.total_hours` should reflect provider-facing hours only, after excluded constraint blocks have been removed.
