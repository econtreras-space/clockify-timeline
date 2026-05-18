# Subagent Evals

This repo uses a contract-first eval harness for the Clockify subagents.

The harness is designed around three ideas:

- invoke the real Claude Code subagent runtime, not a fake prompt shim
- validate machine-checkable contracts before semantic assertions
- prefer invariant checks over brittle full-output snapshots for variable stages

## What It Covers

- isolated subagent fixtures for:
  - `ct-parser`
  - `ct-reconstructor`
  - `ct-validator`
  - `ct-push`
- chain smoke tests for adjacent stage compatibility
- mock push translation with no live Clockify calls

## How It Runs

The runner loads the checked-in subagent markdown files, converts them into inline agent definitions, and invokes Claude Code with:

- `--agent`
- `--agents`
- `--no-session-persistence`

Default local runs do **not** use `--bare`. This lets the harness use the normal Claude Code login flow while still avoiding persisted conversation state.

`--bare-mode` is available for explicit headless use, but it requires `ANTHROPIC_API_KEY`.

## Commands

Self-check the eval library without invoking Claude:

```bash
python3 evals/run_subagent_evals.py --self-check
```

Run all isolated and chain evals:

```bash
python3 evals/run_subagent_evals.py
```

Run only fixtures matching a substring:

```bash
python3 evals/run_subagent_evals.py --match ct-reconstructor
```

Run in explicit bare/headless mode:

```bash
ANTHROPIC_API_KEY=... python3 evals/run_subagent_evals.py --bare-mode
```

## Notes

- Default local runs require a working `claude auth login`.
- Bare mode requires `ANTHROPIC_API_KEY`.
- The runner performs an auth preflight before invoking any subagent.
- Eval artifacts are written to `/tmp/clockify-subagent-evals/`.
- `ct-push` tests use disposable mock scripts and never call the live Clockify API.
