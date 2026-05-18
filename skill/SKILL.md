---
name: clockify-timesheet
description: "Reconstruct a plausible work timeline from EOD narrative and push it to Clockify after explicit user confirmation. Triggers: 'push to clockify', 'log my hours', 'timesheet from slack', 'EOD to clockify', 'fill my clockify', 'log this week', or any request to turn Slack EOD updates into time entries. Also triggers when the user pastes EOD messages without mentioning Clockify explicitly."
---

# Clockify Timesheet Skill — Orchestrator

Converts end-of-day narrative into a plausible, reviewable timeline proposal, then submits it to Clockify after explicit user confirmation.

This file is the **orchestrator only**. It coordinates four subagents — one per pipeline stage — and handles all direct user interaction (review, corrections, clarification Q&A). The orchestrator does not perform domain reasoning itself: it delegates each bounded task to the appropriate subagent and routes on the result.

## V1 Rules

These rules are non-negotiable. They bind both the orchestrator and every subagent.

- **No invented missing days.** Do not reconstruct a workday for which there is no narrative context. (ADR-001, ADR-004)
- **No fabricated work.** Every timeline block must trace back to something described or clearly implied by the narrative. (ADR-004)
- **Schedule defaults are not architecture.** The time-slot template in `config/schedule_defaults.json` is a starting point, not a permanent rule.
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

Leave `project_id` as `null` if you want per-block project mapping or projectless entries. If set, it should be treated as a backwards-compatible fallback only when a provider payload entry omits `project_id`.

Never print, log, or display the API key.

---

## Pipeline

The skill operates in five stages. Stages 1, 2, 3, and 5 are handled by dedicated subagents. Stage 4 (confirm) is handled inline by the orchestrator.

---

### Stage 1 — Parse

**Subagent:** `@ct-parser`

**What to pass:**
- The raw narrative text from the user
- The timezone from `~/.config/clockify/credentials.json` (default: `America/Montevideo`)

**What you receive:** `NarrativeInput[]` — a JSON array, one object per distinct reporting day.

**Orchestrator behavior after receiving the result:**
- If the array is empty, tell the user no reportable days were found and stop.
- If any entry has `"ambiguous": true`, ask the user to confirm the date for that entry before continuing.
- Otherwise, proceed to Stage 2 with the full array.

---

### Stage 2 — Reconstruct

**Subagent:** `@ct-reconstructor`

**Before spawning:** read `skill/config/schedule_defaults.json` and note the `schedule_config_path` to pass to the subagent.

**Spawn one `@ct-reconstructor` per `NarrativeInput`.** For multi-day inputs, spawn them in parallel — each handles one day independently.

**What to pass to each:**
- The single `NarrativeInput` for that day
- The absolute path to `skill/config/schedule_defaults.json`

**What you receive:** one `TimelineProposal` per day.

**Orchestrator behavior after receiving all results:**
- If any proposal has `"needs_clarification": true`, ask the user the `clarification_questions` listed in that proposal. Then re-spawn `@ct-reconstructor` for that day with the original `NarrativeInput` augmented with the user's answers appended to `raw_text`.
- Once all proposals are returned without clarification flags, proceed to Stage 3.

---

### Stage 3 — Validate

**Subagent:** `@ct-validator`

**Spawn one `@ct-validator` per `TimelineProposal`.**

**What to pass:** the `TimelineProposal` JSON for that day.

**What you receive:** `ValidationState` — `{ "outcome", "warnings", "clarification_questions", "rejection_reason" }`.

**Route on outcome:**

| Outcome | Action |
|---|---|
| `pass` | Proceed to Stage 4 |
| `warn` | Proceed to Stage 4; surface all warnings prominently in the review |
| `needs_clarification` | Ask the user the listed `clarification_questions`. Then loop back to Stage 2 for that day with enriched narrative. |
| `reject` | Explain the `rejection_reason` clearly. Ask the user to provide better context or skip the day. Do not proceed. |

---

### Stage 4 — Confirm (inline — no subagent)

Stage 4 runs entirely in the orchestrator's context.

**Display the proposal:**

Render the proposal inline in the conversation. Show each day's blocks in chronological order, and if the validation outcome was `warn`, include all warnings prominently at the top.

Ask explicitly:

> **Does this look right? Reply yes to push to Clockify, or tell me what to change.**

**Accept these responses:**
- **"yes" / "looks good" / any clear affirmative** → proceed to Stage 5
- **A correction or modification** → update the proposal accordingly and re-display. If the change is significant (adding/removing a task, changing a day's structure), re-spawn `@ct-reconstructor` with the corrected narrative. Then re-validate with `@ct-validator` before re-displaying.
- **"skip" / "cancel" / "no"** → abort without pushing. Acknowledge clearly.

Never proceed to Stage 5 without an explicit affirmative.

---

### Stage 5 — Push

**Subagent:** `@ct-push`

**Spawn after user confirmation.**

**What to pass:**
- The confirmed `TimelineProposal` JSON
- The absolute path to the project root (e.g. `/Users/edgarcontreras/Documents/space-chapters/Automations/clockify-timeline`)

**What you receive:** `{ "entries_pushed", "entries_failed", "timesheet_saved", "timesheet_path", "errors" }`

`@ct-push` is responsible for translating any block-level `project_key` values into Clockify project IDs using `skill/config/schedule_defaults.json`. Blocks without a clear project remain projectless and are still valid to push.

**Report to the user:** total pushed, total failed, whether the timesheet backup was saved, and any errors.

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
| Narrative too vague to reconstruct | Trigger clarification (Stage 2 → 3 loop). Do not guess. |
| Subagent returns malformed JSON | Log the raw output and ask the user whether to retry or abort. |

---

## Subagent Map

| Subagent | File | Stage | Tools | Model |
|---|---|---|---|---|
| `ct-parser` | `.claude/agents/clockify-timesheet/ct-parser.md` | 1 — Parse | Read | haiku |
| `ct-reconstructor` | `.claude/agents/clockify-timesheet/ct-reconstructor.md` | 2 — Reconstruct | Read | sonnet |
| `ct-validator` | `.claude/agents/clockify-timesheet/ct-validator.md` | 3 — Validate | none | haiku |
| `ct-push` | `.claude/agents/clockify-timesheet/ct-push.md` | 5 — Push | Bash, Write | haiku |

## File Map

```
skill/
├── SKILL.md                     ← this file — orchestrator
├── config/
│   └── schedule_defaults.json   ← workday shape, read by ct-reconstructor
└── scripts/
    ├── push_clockify.py         ← executed by ct-push (Clockify API)
    ├── generate_timesheet.py    ← executed by ct-push (XLSX/CSV backup)
    ├── validate_credentials.py  ← run on startup to verify API key
    └── requirements.txt         ← openpyxl (optional, for XLSX output)
```
