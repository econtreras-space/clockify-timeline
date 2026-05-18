---
name: clockify-timesheet
description: "Reconstruct a plausible work timeline from EOD narrative and push it to Clockify after explicit user confirmation. Triggers: 'push to clockify', 'log my hours', 'timesheet from slack', 'EOD to clockify', 'fill my clockify', 'log this week', or any request to turn Slack EOD updates into time entries. Also triggers when the user pastes EOD messages without mentioning Clockify explicitly."
---

# Clockify Timesheet Skill

Converts end-of-day narrative into a plausible, reviewable timeline proposal, then submits it to Clockify after explicit user confirmation.

## V1 Rules

These rules are non-negotiable. They are derived from the architectural decisions recorded in `docs/decisions/`.

- **No invented missing days.** Do not reconstruct a workday for which there is no narrative context. (ADR-001, ADR-004)
- **No fabricated work.** Every timeline block must trace back to something described or clearly implied by the narrative. (ADR-004)
- **Schedule defaults are not architecture.** The time-slot template in `config/schedule_defaults.json` is a starting point, not a permanent rule. (ADR-005)
- **User confirmation is mandatory.** Never push to Clockify without an explicit "yes" from the user. (ADR-003)
- **User authority is final.** If the user corrects, modifies, or rejects any part of a proposal, accept it without argument. (ADR-001)

---

## Credentials

Read from `~/.config/clockify/credentials.json`. If the file is missing, tell the user to create it:

```bash
mkdir -p ~/.config/clockify
cat > ~/.config/clockify/credentials.json << 'EOF'
{
  "api_key": "YOUR_CLOCKIFY_API_KEY",
  "workspace_id": "YOUR_WORKSPACE_ID",
  "project_id": null,
  "timezone": "America/Montevideo"
}
EOF
chmod 600 ~/.config/clockify/credentials.json
```

Never print, log, or display the API key.

---

## Pipeline

The skill operates in five explicit stages. Each stage has a clear input, output, and behavioral contract. Do not blend stages.

---

### Stage 1 — Parse

**Input:** Raw narrative text pasted by the user (Slack EOD messages, freeform notes, etc.)
**Output:** One `NarrativeInput` per reporting day

**Behavior:**
1. Identify the date(s) being reported. Ask if ambiguous.
2. Read the timezone from `credentials.json` (default: `America/Montevideo`).
3. Treat each distinct day as a separate `NarrativeInput`. Multi-day inputs produce multiple inputs.
4. Do not interpret or assign time at this stage — just structure the input.
5. If there is no narrative for a day (e.g. a missing weekday in a weekly report), **do not fabricate a NarrativeInput for it**. Skip that day and note it explicitly.

---

### Stage 2 — Reconstruct (Analyzer)

**Input:** `NarrativeInput` + `Constraint[]` + `AvailableGap[]` (from `pipeline/constraint_builder.py`)
**Output:** `TimelineProposal` (draft, not yet validated)
**Contract:** `docs/prompts/analyzer-contract.md`

**Behavior:**
1. Load schedule constraints and available gaps using `pipeline/constraint_builder.py`.
2. Optionally fetch calendar constraints via `adapters/calendar/adapter.py` (stub in V1).
3. **Semantic extraction** — use the prompt template in `analyzer/semantic_extractor.py` to extract `WorkUnit` candidates from the narrative. Do not assign time yet.
4. **Uncertainty assessment** — use `analyzer/uncertainty.py` to score narrative quality and assess allocation surface. If `should_clarify()` returns True, skip to Stage 3 immediately with a clarification request.
5. **Temporal reconstruction** — use the prompt template in `analyzer/temporal_reconstructor.py` to distribute `WorkUnit` candidates into `TimelineBlock` allocations within the available gaps.
6. Assemble the `TimelineProposal` from the resulting blocks.

**Key invariants (from analyzer contract):**
- Allocate only within described work and available gaps.
- Never reconstruct an entire unreported weekday.
- Surface confidence and ambiguity explicitly — do not hide uncertainty.
- Prefer operational noise (realistic fragmentation) over robotic uniform blocks.

---

### Stage 3 — Validate

**Input:** `TimelineProposal` (draft)
**Output:** `ValidationState` — one of: `pass`, `warn`, `needs_clarification`, `reject`
**Contract:** `docs/prompts/validation-contract.md` + `docs/prompts/clarification-contract.md`

**Behavior:**
1. Run `pipeline/validator.py` on the proposal.
2. Based on the outcome:
   - **PASS** → proceed to Stage 4.
   - **WARN** → proceed to Stage 4, but surface all warnings prominently in the review.
   - **NEEDS_CLARIFICATION** → stop. Use `pipeline/proposal_formatter.py:format_clarification_request()` to generate targeted questions. Wait for user response, then loop back to Stage 2 with the new context added to the narrative.
   - **REJECT** → do not proceed. Explain the rejection reason clearly. Ask the user to provide better context or skip the day.

**What validation checks:**
- No empty proposals (no invented days).
- Total hours within plausible bounds.
- No blocks overlapping hard constraints (especially lunch break).
- Low-confidence block ratio.
- Blocks within workday boundary.

---

### Stage 4 — Confirm

**Input:** `TimelineProposal` with attached `ValidationState` (PASS or WARN)
**Output:** User-approved proposal, or a correction that loops back to Stage 2
**Contract:** `docs/prompts/proposal-generation.md`

**Behavior:**
1. Use `pipeline/proposal_formatter.py:format_proposal()` to render the proposal for review.
2. Display the formatted proposal to the user. Include all warnings.
3. Ask explicitly: **"Does this look right? Reply yes to push to Clockify, or tell me what to change."**
4. Accept:
   - **"yes" / "looks good" / confirmation** → proceed to Stage 5.
   - **Correction or modification** → update the proposal accordingly and re-display for confirmation (may loop back to Stage 2 if changes are significant).
   - **"skip" / "cancel"** → abort without pushing.
5. Never proceed to Stage 5 without an explicit affirmative response.

---

### Stage 5 — Push

**Input:** User-confirmed `TimelineProposal`
**Output:** Clockify submission result + XLSX backup
**Contract:** `docs/providers/clockify-adapter.md`

**Behavior:**
1. Translate the proposal into a `ProviderPayload` using `adapters/clockify/adapter.py:to_provider_payload()`.
2. Serialize to the dict format using `adapters/clockify/adapter.py:payload_to_json_dict()`.
3. Save the payload JSON to `/home/claude/clockify_entries.json`.
4. Run the push script via `adapters/clockify/client.py:push()`:
   ```bash
   python3 skill/scripts/push_clockify.py /home/claude/clockify_entries.json
   ```
5. Generate the XLSX backup:
   ```bash
   python3 skill/scripts/generate_timesheet.py /home/claude/clockify_entries.json /mnt/user-data/outputs/timesheet.xlsx
   ```
6. Report results: total pushed, total failed, any failed entries.

**Dry-run mode:** Pass `dry_run=True` to `client.push()` or append `--dry-run` to preview without submitting.

---

## Error Handling

| Condition | Response |
|---|---|
| Missing credentials file | Tell user to create it. Show setup command. Do not print key values. |
| Invalid API key (401) | Ask user to check their key in Clockify profile settings. |
| Rate limiting (429) | Script retries up to 3 times with backoff. |
| Duplicate entry | Script skips and logs a warning. |
| Network error | Logged per-entry. Batch continues. |
| Missing narrative for a day | Skip that day. Note it explicitly. Do not invent content. |
| Narrative too vague to reconstruct | Trigger clarification (Stage 3). Do not guess. |

---

## Component Map

```
skill/
├── SKILL.md                     ← this file — orchestration layer
├── domain/types.py              ← NarrativeInput, WorkUnit, Constraint, TimelineProposal, etc.
├── config/schedule_defaults.json ← workday shape (configurable defaults)
├── analyzer/
│   ├── semantic_extractor.py    ← narrative → WorkUnit candidates
│   ├── temporal_reconstructor.py ← WorkUnits → TimelineBlocks
│   └── uncertainty.py           ← confidence scoring + clarification triggers
├── pipeline/
│   ├── constraint_builder.py    ← config + calendar → Constraints + AvailableGaps
│   ├── validator.py             ← TimelineProposal → ValidationState
│   └── proposal_formatter.py   ← proposal → human-readable review text
└── adapters/
    ├── clockify/
    │   ├── adapter.py           ← TimelineProposal → Clockify JSON
    │   └── client.py           ← push script wrapper
    └── calendar/
        └── adapter.py          ← calendar events → Constraints (V1 stub)
```

Existing `scripts/` are unchanged. The adapter layer wraps them.
