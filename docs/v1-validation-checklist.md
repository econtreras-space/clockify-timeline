# V1 Validation Checklist

Back to [Docs Home](./README.md), [Architectural Principles](./blueprint/architectural-principles.md), [Architecture Decisions](./decisions/README.md), and [Prompt Contracts](./prompts/README.md).

## Purpose

This checklist defines the recommended implementation order for reaching a real V1 quickly while preserving the architecture already documented in this wiki.

It is optimized for early validation, not long-term polish.

## Guiding Corrections

The current implementation direction must respect three explicit constraints:

- the system must not recreate missing workdays with invented context-based tasks
- fixed daily schedule defaults are temporary and should move into configurable rules
- final provider-facing payloads should stay provider-aligned and owned by the adapter boundary rather than redefined in core docs

## Recommended Order

### 1. Lock the Real V1 Rules

Before refining prompts or scripts further, freeze the actual V1 rules that the system is allowed to enforce.

The first rule set should make the following explicit:

- no invented missing weekdays
- no fabricated work that is absent from the narrative
- schedule assumptions are defaults, not permanent architecture
- user confirmation is mandatory before provider handoff

This step matters because undocumented “helpful defaults” are currently the fastest path to domain drift.

### 2. Define the Minimal Internal Contracts

Before adding detailed prompt contracts, make sure the internal shapes are stable enough to support the pipeline.

The minimum set to stabilize is:

- parsed narrative result
- normalized `WorkUnit` output
- proposal-level structure before provider translation
- validation result shape

These do not replace provider-aligned payloads. They protect the internal system from being shaped by provider formats too early.

### 3. Write the Validation Contract First

The first prompt-side contract to formalize should be [Validation Contract](./prompts/validation-contract.md).

This should define:

- what must always be true before a proposal can move forward
- what conditions produce warnings
- what conditions require clarification
- what conditions force refusal or regeneration

This is the fastest way to prevent weak output from looking “good enough” too early.

### 4. Write the Analyzer Contract Second

Once validation behavior is clear, formalize [Analyzer Contract](./prompts/analyzer-contract.md).

This should define:

- what the analyzer is allowed to infer
- what it must not invent
- what inputs it requires
- what outputs it must produce
- how ambiguity should surface into downstream validation

This turns the analyzer from a fuzzy prompt into a bounded subsystem.

### 5. Separate the Real Pipeline Stages in the Skill

Even if the implementation stays in one skill file at first, the operating stages should be made explicit:

- parse
- reconstruct
- validate
- confirm
- push

If these remain blended together, the wiki can keep improving while the implementation stays operationally ambiguous.

### 6. Write the Clarification Contract Third

After validation and analyzer responsibilities are bounded, formalize [Clarification Contract](./prompts/clarification-contract.md).

This should define:

- when the system must stop and ask
- what kinds of follow-up questions are acceptable
- how clarification differs from fabrication
- how regeneration should be triggered after new context arrives

### 7. Write the Proposal Generation Contract Fourth

The last of the initial prompt contracts should be [Proposal Generation](./prompts/proposal-generation.md).

This should describe how validated internal structures become a reviewable proposal before provider translation.

It belongs later because it depends on the earlier contracts being stable.

## What to Avoid During V1

- Do not make provider payloads the center of the system.
- Do not let the skill invent full missing days to satisfy a weekly target.
- Do not treat fixed schedule assumptions as architecture.
- Do not add large prompt prose before the validation boundary is clear.
- Do not optimize for polished automation before testing correction and confirmation loops.

## Minimal Success Criteria for V1

V1 is successful if the system can:

- accept real narrative input
- reconstruct only from described or defensible context
- apply configurable schedule rules
- produce a reviewable proposal
- reject or clarify weak cases
- require explicit confirmation
- hand off accepted output to the Clockify adapter cleanly

## Suggested Execution Sequence

If you want a strict “do this next” order:

1. stabilize V1 rules
2. stabilize internal contracts
3. implement validation contract
4. implement analyzer contract
5. refactor the skill into explicit stages
6. implement clarification contract
7. implement proposal generation contract
8. validate the end-to-end flow with real samples

---

## Runtime Issues Found (2026-05-18)

Issues discovered during the first real end-to-end push run. Both caused Stage 5 failures after a fully valid proposal.

### Issue 1 — Payload schema mismatch between skill and push script

**What happened:** `push_clockify.py` failed with `KeyError: 'entries'` on the first push attempt.

**Root cause:** The skill assembled the JSON payload with a nested structure (`payload.entries`), but `push_clockify.py` reads from the top level (`data[“entries”]`). No contract enforced the shape between them.

**Workaround applied:** Rewrote the payload to a flat `{ “entries”: [...] }` structure matching the script's expectation.

**What this reveals:** The adapter boundary is not yet formally specified. The push script's expected input shape is undocumented — it is effectively an implicit contract. This violates the intent of step 3 of the Recommended Order (define internal contracts before the adapter consumes them).

**Action needed:** Document the exact JSON schema that `push_clockify.py` expects as part of the [Clockify Adapter Contract](./providers/clockify-adapter.md). The skill must produce this shape before calling Stage 5.

---

### Issue 2 — Missing `openpyxl` dependency for XLSX backup ✓ Resolved

**What happened:** `generate_timesheet.py` failed with `ModuleNotFoundError: No module named 'openpyxl'`.

**Root cause:** `openpyxl` is required by the XLSX backup script but is not installed in the default Python environment. The original auto-install fallback (`os.system("pip install ...")`) is broken on PEP 668-managed environments (macOS Homebrew Python 3.13+, Debian 12+) and does not work within the same process even when the install succeeds.

**Resolution:** `generate_timesheet.py` was refactored with a stdlib-first approach:
- Removed the runtime auto-install block entirely
- Added a `write_csv` fallback using the stdlib `csv` module — no dependencies required
- Script now tries `openpyxl` → XLSX; falls back gracefully to CSV with a clear notice
- Added input schema validation (`"entries"` key guard) and file-write error handling
- `skill/scripts/requirements.txt` created, listing `openpyxl` as optional

**Known limitation (V2):** XLSX row styling uses string-matching on description text to detect constraint types (e.g., `"lunch"`, `"standup"`). This is brittle. A future improvement should add an optional `"type"` field to payload entries (sourced from `schedule_defaults.json` constraint definitions) so the script can branch on type rather than description text.

---

## Technical Gaps and Open Questions (2026-05-18)

A broader review of the project following the first real run. These are structural gaps between what is documented and what is actually wired together. This section exists as a reference guideline — not as an implementation task list — to inform the ongoing portability work.

### A. Technical Gaps

Gaps are listed in order of severity. Each entry describes what exists, what is missing, and the consequence if left unaddressed.

#### Gap 1 — No unified skill orchestration entry point

SKILL.md defines five explicit stages (parse → reconstruct → validate → confirm → push), but no Claude Code skill file ties them together as an executable flow. The stages exist as documented intent. There is no `clockify-timesheet` entry point that routes through the full pipeline in sequence.

**Consequence:** Each stage runs in isolation or mentally. The skill cannot be invoked end-to-end by a user without manual navigation through each stage.

#### Gap 2 — Python runtime dependencies are undeclared at the skill level

`skill/scripts/requirements.txt` lists only `openpyxl` — discovered at runtime, not upfront. The `skill/` modules (`domain/`, `analyzer/`, `pipeline/`, `adapters/`) import each other, but the Python path setup and venv activation are entirely undocumented. No install step exists in `README.md`, `SKILL.md`, or any onboarding document.

**Consequence:** Any fresh environment fails before Stage 2 runs. A developer following the docs cannot reproduce the setup independently.

#### Gap 3 — Prompt contracts are not integrated into live Claude calls

`semantic_extractor.py` and `temporal_reconstructor.py` contain prompt templates (`EXTRACTION_PROMPT`, `RECONSTRUCTION_PROMPT`). These are string constants, not wired calls. Claude is not being invoked by these scripts — they are placeholders awaiting integration.

**Consequence:** Stage 2 (reconstruct) is architecturally described but not executing. The domain model is populated manually or not at all during a real run.

#### Gap 4 — Proposal formatter is stubbed, not implemented

`skill/pipeline/proposal_formatter.py` exists but contains no formatting logic. Stage 4 (confirm) depends on a human-readable proposal being generated from a `TimelineProposal` object.

**Consequence:** The confirm loop cannot function in its current state. A user cannot review or approve a proposal that was never rendered.

#### Gap 5 — Clarification loop has no implementation path

`validator.py` correctly returns `NEEDS_CLARIFICATION` with a list of questions when the proposal is ambiguous. No mechanism exists to surface those questions to the user, collect a response, and re-enter Stage 2 with enriched context.

**Consequence:** `NEEDS_CLARIFICATION` is effectively a terminal state when it should be a continuation. The system drops the pipeline instead of asking.

#### Gap 6 — Adapter payload contract is implicit

`push_clockify.py` expects a specific flat JSON shape. This was not formally documented before the first run. The schema mismatch (Issue 1 above) was fixed by trial and error, not by a defined contract visible to both the skill and the script.

**Consequence:** Any future change to how the skill assembles the payload can silently break the push boundary again. The adapter boundary exists in code but not in a verifiable, enforceable contract.

---

### B. Open Questions

These are unresolved design decisions that affect portability. Each question describes the tension and what needs to be settled before or during the portability work.

#### Question 1 — Is a Claude Code skill the right deployment surface for company-wide rollout?

**Fits:** Direct Claude reasoning access, synchronous human-in-the-loop confirmation, no separate service layer, no credentials stored in a remote system.

**Risks:** No persistent state across context resets, synchronous-only execution, dependency management is manual per developer, prompt stages are difficult to test in isolation without a full Claude Code session.

**What needs to be decided:** For a company-wide rollout across technical and non-technical team members, does the skill surface hold — or does this need to run as a standalone CLI backed by Anthropic SDK calls, with the skill acting only as a thin launcher?

#### Question 2 — How should the skill handle session state if the context resets mid-pipeline?

The five-stage pipeline is stateful: a `TimelineProposal` built in Stage 2 must survive intact through Stage 4 confirmation. Claude Code context is ephemeral — a reset between stages means the proposal is lost and the pipeline must restart from the narrative.

**What needs to be decided:** Should proposals be checkpointed to a temp file (e.g. `/tmp/clockify_proposal.json`) after Stage 2, so Stage 4 and Stage 5 can resume without re-running the full reconstruction?

#### Question 3 — How should Python dependencies be managed for portability?

A company-wide skill must work on any developer's machine without requiring manual setup steps. The current state (undocumented venv, partial `requirements.txt`) does not meet that bar.

**Options to evaluate:** bundle a `setup.sh` that creates a venv and installs dependencies; use a `pyproject.toml` with a declared entry point; or restructure scripts to use only stdlib plus direct HTTP calls to the Clockify API, eliminating most dependencies.

**What needs to be decided:** What is the acceptable setup friction for a non-technical user running this skill for the first time?

#### Question 4 — Should the analyzer stages call Claude via the Anthropic SDK, or rely on the skill's own reasoning context?

The current design implies Claude reasons about semantic extraction and temporal reconstruction within the skill's own context window — no external API call. But `semantic_extractor.py` and `temporal_reconstructor.py` are standalone Python files that cannot invoke Claude natively; they are prompt templates waiting for a caller.

**What needs to be decided:** Do these scripts become Claude-side reasoning steps (the skill reasons through them directly using its prompt contracts), or do they become SDK-calling Python processes that make their own Anthropic API requests?

#### Question 5 — What is the correct boundary between the Claude skill and the Python scripts?

The current split is: Claude orchestrates, Python scripts handle I/O (push, XLSX backup, credential check). But the domain model, analyzer, and pipeline are also in Python — meaning Claude would need to invoke Python for core domain logic too, not just I/O.

**What needs to be decided:** Should the Python layer be reduced to pure I/O while the domain logic (semantic extraction, temporal reconstruction, validation) lives entirely within Claude's reasoning — expressed as prompt contracts, not Python classes?
