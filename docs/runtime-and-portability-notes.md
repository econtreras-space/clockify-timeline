# Runtime and Portability Notes

## Purpose

This page captures lessons from real runs, current structural risks, and unresolved rollout questions.

It is intentionally separate from the [V1 Validation Checklist](./v1-validation-checklist.md), which focuses on implementation order rather than runtime postmortems.

## Runtime Issues Found (2026-05-18)

Issues discovered during the first real end-to-end push run. Both happened after a fully valid proposal reached Stage 5.

### Issue 1 - Payload schema mismatch between skill and push script

**What happened:** `push_clockify.py` failed with `KeyError: 'entries'` on the first push attempt.

**Root cause:** The skill assembled the JSON payload with a nested structure (`payload.entries`), but `push_clockify.py` reads from the top level (`data["entries"]`). No visible contract enforced the shape between them.

**Workaround applied:** The payload was rewritten to a flat `{ "entries": [...] }` structure matching the script's expectation.

**What this revealed:** The adapter boundary was implicit in code before it was explicit in docs. The skill and the script were coupled by an undocumented payload shape.

**Follow-up:** The expected JSON shape is now documented in the [Clockify Adapter](./providers/clockify-adapter.md).

### Issue 2 - Missing `openpyxl` dependency for XLSX backup

**What happened:** `generate_timesheet.py` failed with `ModuleNotFoundError: No module named 'openpyxl'`.

**Root cause:** `openpyxl` is required by the XLSX backup script but is not installed in the default Python environment. The original runtime auto-install fallback was not portable and could not reliably recover within the same process.

**Resolution:** `generate_timesheet.py` was refactored with a stdlib-first approach:

- removed the runtime auto-install block entirely
- added a `write_csv` fallback using the stdlib `csv` module
- made the script try `openpyxl` first and fall back to CSV with a clear notice
- added input schema validation for the `"entries"` key
- added file-write error handling
- added `skill/scripts/requirements.txt` with `openpyxl` listed as optional

**Known limitation:** XLSX row styling still relies on matching description text for constraint types such as `"lunch"` or `"standup"`. A future improvement could add an optional payload `"type"` field so the exporter branches on explicit metadata instead of description text.

## Current Structural Risks

These are the current architecture-to-runtime risks worth keeping visible as the project evolves.

### 1. Keep the orchestration entry point honest

`skill/SKILL.md` now acts as the executable orchestration entry point. The remaining risk is drift between that live contract, the subagent prompts, and the surrounding docs.

**Why it matters:** The architecture can look stage-based on paper while behaving inconsistently in practice.

### 2. Keep Python dependency expectations explicit

The current design keeps Python mostly at the provider and export edge, which is healthier than the older mixed model. The remaining portability concern is still onboarding clarity around optional script dependencies.

**Why it matters:** Fresh environments may still stumble at the provider edge even if the Claude-side pipeline is correct.

### 3. Keep prompt contracts aligned with live prompts

The prompt contracts live as documentation while runtime behavior lives in the subagent prompt files. The risk is no longer missing integration; it is silent divergence over time.

**Why it matters:** The wiki can become authoritative in appearance while the real agent behavior drifts elsewhere.

### 4. Keep proposal rendering inside the orchestrator contract

The current V1 flow renders proposals inline rather than through a Python formatter module. The remaining risk is inconsistency in how proposals are displayed for review and correction.

**Why it matters:** Confirmation can remain technically possible while review quality becomes uneven.

### 5. Keep clarification as a real continuation path

The current orchestrator contract includes the clarification loop. The remaining risk is losing fidelity between clarification answers, reconstructed narrative, and the next validation pass.

**Why it matters:** Clarification can exist nominally while the enriched retry path becomes unreliable.

### 6. Keep the adapter payload contract explicit

`push_clockify.py` expects a specific flat JSON shape. That contract now exists in the docs, but it still needs to remain visible and enforced whenever the push boundary changes.

**Why it matters:** Future payload changes can silently break Stage 5 if the skill and adapter evolve independently.

## Open Portability Questions

These are unresolved decisions that affect rollout, maintenance, and operational safety.

### Question 1 - Is a Claude Code skill the right deployment surface for company-wide rollout?

**Fits:** Direct Claude reasoning access, synchronous human-in-the-loop confirmation, no separate service layer, and no credentials stored in a remote system.

**Risks:** No persistent state across context resets, synchronous-only execution, manual dependency management per developer, and limited stage-level testability without a full Claude Code session.

### Question 2 - How should the skill handle session state if the context resets mid-pipeline?

The five-stage pipeline is stateful: a `TimelineProposal` built in Stage 2 must survive intact through Stage 4 confirmation. Claude Code context is ephemeral, so a reset between stages loses the in-flight proposal.

**Decision to make:** Whether proposals should be checkpointed to a temp file such as `/tmp/clockify_proposal.json` after Stage 2.

### Question 3 - How should Python dependencies be managed for portability?

A company-wide skill should work on a fresh machine without requiring hidden setup steps. The current state is better than before, but still lightweight and manual.

**Options to evaluate:** a setup script that creates a venv, a `pyproject.toml` with a declared entry point, or further reducing the scripts toward stdlib-only behavior.

### Question 4 - Where should Claude reasoning live if the system outgrows the skill surface?

The current design assumes semantic extraction and temporal reconstruction happen inside the skill's own reasoning context. If that stops being sufficient, the next question is whether those stages stay Claude-side or move to an SDK-backed process.

### Question 5 - What is the durable boundary between the Claude skill and the Python scripts?

The healthiest current split is: Claude owns orchestration and reasoning, Python owns provider I/O and export. The remaining question is whether that boundary stays stable as portability work continues.

## Related Pages

- [Agent-Based Orchestration](./blueprint/agent-orchestration.md)
- [Clockify Adapter](./providers/clockify-adapter.md)
- [V1 Validation Checklist](./v1-validation-checklist.md)
