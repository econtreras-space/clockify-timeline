# Clockify Timeline

An AI-assisted timesheet reconstruction tool. You paste your end-of-day narrative — Slack messages, freeform notes, anything — and it proposes a plausible work timeline for your review. You confirm it, and it pushes to Clockify.

The system never submits anything without your explicit approval. It reconstructs only what you described. It asks clarifying questions when the narrative is too thin to produce a believable proposal.

> For the architecture map and reading paths, start with [docs/README.md](docs/README.md).

---

## How It Works

The skill runs as a Claude Code command. When triggered, it walks through five stages:

1. **Parse** — structures your narrative into one input per reporting day
2. **Reconstruct** — the Analyzer extracts what you worked on and distributes it into time blocks
3. **Validate** — checks the proposal for plausibility and constraint violations; asks questions if it can't proceed confidently
4. **Confirm** — shows you the full proposal and waits for your explicit approval
5. **Push** — translates the approved proposal to Clockify's format and submits it

> See [docs/blueprint/operational-pipeline.md](docs/blueprint/operational-pipeline.md) for the full step-by-step flow.

---

## Setup

### 1. Get your Clockify credentials

You'll need two values from your Clockify account:

- **API key** — Clockify → Profile Settings → API Key
- **Workspace ID** — Clockify → Workspace Settings → General (visible in the URL)

### 2. Create the credentials file

```bash
mkdir -p ~/.config/clockify
cat > ~/.config/clockify/credentials.json << 'EOF'
{
  "api_key": "YOUR_API_KEY_HERE",
  "workspace_id": "YOUR_WORKSPACE_ID_HERE",
  "project_id": null,
  "timezone": "America/Montevideo"
}
EOF
chmod 600 ~/.config/clockify/credentials.json
```

`project_id` is optional legacy config and is not used by the provider adapter for V1 routing. Leave it `null`. Per-entry project mapping happens from internal `project_key` values through `skill/config/schedule_defaults.json`, and entries may remain projectless. Set `timezone` to your local timezone (e.g. `America/New_York`, `Europe/Madrid`).

### 3. Validate the setup

```bash
python3 skill/scripts/validate_credentials.py
```

This checks that the file exists, the JSON is valid, the API key works, and the workspace is accessible. It never prints your actual key.

---

## Usage

Trigger the skill from Claude Code with any of these phrases:

- `push to clockify`
- `log my hours`
- `EOD to clockify`
- `timesheet from slack`

Then paste your EOD narrative. The skill handles the rest.

**Example input:**

```
Monday: worked on the sync layer refactor most of the morning, reviewed two PRs in the afternoon, had the usual standup, spent the last hour on incident follow-up notes.
```

The system will propose a timeline, show it to you for review, and wait for your confirmation before pushing anything.

---

## Customize the Schedule

The default workday shape — working hours, standup time, lunch break — lives in:

```
skill/config/schedule_defaults.json
```

Edit it to match your actual schedule. These are defaults, not fixed rules.

---

## Project Structure

```
skill/                  Main skill and all components
├── SKILL.md            Orchestration layer — how the pipeline runs
├── config/             Schedule defaults
├── scripts/            Low-level API scripts (push, generate XLSX, validate creds)

docs/                   Architecture and design documentation
.claude/agents/clockify-timesheet/
├── ct-parser.md         Parse stage prompt
├── ct-reconstructor.md  Reconstruct stage prompt
├── ct-validator.md      Validate stage prompt
└── ct-push.md           Push stage prompt
example/                Sample JSON output files
```

---

## Documentation

| What you want to understand | Where to look |
|---|---|
| How to read the architecture docs quickly | [docs/README.md](docs/README.md) |
| Why the system works this way | [docs/blueprint/system-vision.md](docs/blueprint/system-vision.md) |
| How the pieces fit together | [docs/blueprint/high-level-architecture.md](docs/blueprint/high-level-architecture.md) |
| The full pipeline step by step | [docs/blueprint/operational-pipeline.md](docs/blueprint/operational-pipeline.md) |
| How the current V1 runtime is actually wired | [docs/blueprint/agent-orchestration.md](docs/blueprint/agent-orchestration.md) |
| What each domain concept means | [docs/domain/domain-overview.md](docs/domain/domain-overview.md) |
| How the Analyzer reasons | [docs/analyzer/analyzer-overview.md](docs/analyzer/analyzer-overview.md) |
| Architectural decisions and their rationale | [docs/decisions/README.md](docs/decisions/README.md) |
| How the Clockify adapter works | [docs/providers/clockify-adapter.md](docs/providers/clockify-adapter.md) |
| Runtime lessons and portability concerns | [docs/runtime-and-portability-notes.md](docs/runtime-and-portability-notes.md) |
| Key terms | [docs/blueprint/glossary.md](docs/blueprint/glossary.md) |
