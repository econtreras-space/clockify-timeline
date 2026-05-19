#!/usr/bin/env python3
"""Contract-first eval harness for the Clockify subagents."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
EVALS_ROOT = ROOT / "evals"
FIXTURES_ROOT = EVALS_ROOT / "fixtures"
SCHEMAS_ROOT = EVALS_ROOT / "schemas"
AGENTS_ROOT = ROOT / ".claude" / "agents" / "clockify-timesheet"
ARTIFACTS_ROOT = Path("/tmp/clockify-subagent-evals")
SCHEDULE_CONFIG_PATH = ROOT / "skill" / "config" / "schedule_defaults.json"

SCHEMA_BY_AGENT = {
    "ct-parser": "narrative_inputs.schema.json",
    "ct-reconstructor": "timeline_proposal.schema.json",
    "ct-validator": "validation_state.schema.json",
    "ct-push": "push_result.schema.json",
}

TOOL_RUNTIME_PATTERNS = [
    "sandbox environment restrictions",
    "cannot directly execute",
    "cannot execute the push",
    "cannot run the push script",
    "unable to execute",
]


class EvalFailure(Exception):
    def __init__(self, category: str, message: str, excerpt: str | None = None):
        super().__init__(message)
        self.category = category
        self.message = message
        self.excerpt = excerpt


@dataclass
class RunOptions:
    bare_mode: bool
    verbose: bool
    show_passing_usage: bool
    strict_output: bool
    max_failures: int | None


@dataclass
class UsageStats:
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    duration_ms: int = 0


@dataclass
class ClaudeInvocation:
    payload: Any
    wrapper: dict[str, Any] | None
    raw_stdout: str
    raw_stderr: str
    result_text: str
    extraction_warning: str | None
    usage: UsageStats
    command: list[str]


@dataclass
class EvalResult:
    name: str
    status: str
    category: str | None
    message: str
    artifact_dir: Path
    usage: UsageStats
    warnings: list[str] = field(default_factory=list)


def load_json(path: Path) -> Any:
    with path.open() as handle:
        return json.load(handle)


def save_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def save_json(path: Path, value: Any) -> None:
    save_text(path, json.dumps(value, indent=2, sort_keys=True))


def parse_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text()
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not match:
        raise EvalFailure("expectation_failure", f"{path} does not contain YAML frontmatter")

    raw_frontmatter, body = match.groups()
    data: dict[str, Any] = {"prompt": body.strip()}

    for line in raw_frontmatter.splitlines():
        if not line.strip():
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        if key == "tools":
            data[key] = [tool.strip() for tool in value.split(",")] if value else []
        else:
            data[key] = value
    return data


def build_inline_agent(agent_name: str) -> dict[str, Any]:
    frontmatter = parse_frontmatter(AGENTS_ROOT / f"{agent_name}.md")
    agent_def: dict[str, Any] = {
        "description": frontmatter.get("description", agent_name),
        "prompt": frontmatter["prompt"],
    }
    if "tools" in frontmatter:
        agent_def["tools"] = frontmatter["tools"]
    if "model" in frontmatter:
        agent_def["model"] = frontmatter["model"]
    return {agent_name: agent_def}


def parse_hhmm(value: str) -> int:
    hours, minutes = value.split(":")
    return int(hours) * 60 + int(minutes)


def nearly_equal(left: float, right: float, epsilon: float = 0.02) -> bool:
    return math.isclose(left, right, abs_tol=epsilon)


def first_json_value(text: str) -> Any | None:
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char not in "[{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
            return value
        except json.JSONDecodeError:
            continue
    return None


def extract_payload_text(result_text: str, strict_output: bool) -> tuple[Any, str | None]:
    stripped = result_text.strip()
    if not stripped:
        raise EvalFailure("json_extraction_failure", "assistant result was empty")

    try:
        return json.loads(stripped), None
    except json.JSONDecodeError:
        pass

    fenced_blocks = re.findall(r"```(?:json)?\s*(.*?)```", stripped, re.DOTALL | re.IGNORECASE)
    for block in fenced_blocks:
        candidate = block.strip()
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        warning = "Recovered JSON from fenced block instead of clean JSON-only output."
        if strict_output:
            raise EvalFailure("expectation_failure", warning, excerpt=stripped[:400])
        return payload, warning

    payload = first_json_value(stripped)
    if payload is not None:
        warning = "Recovered JSON embedded in surrounding prose instead of clean JSON-only output."
        if strict_output:
            raise EvalFailure("expectation_failure", warning, excerpt=stripped[:400])
        return payload, warning

    raise EvalFailure("json_extraction_failure", "unable to recover JSON from assistant result", excerpt=stripped[:400])


def validate_schema(value: Any, schema: Any, path: str = "$") -> None:
    if not isinstance(schema, dict):
        raise EvalFailure("schema_failure", f"unsupported schema node at {path}")

    if "type" in schema:
        expected_types = schema["type"]
        if not isinstance(expected_types, list):
            expected_types = [expected_types]
        if not any(matches_type(value, expected) for expected in expected_types):
            raise EvalFailure("schema_failure", f"{path}: expected {expected_types}, got {type(value).__name__}")

    if "const" in schema and value != schema["const"]:
        raise EvalFailure("schema_failure", f"{path}: expected const {schema['const']!r}, got {value!r}")

    if "enum" in schema and value not in schema["enum"]:
        raise EvalFailure("schema_failure", f"{path}: expected one of {schema['enum']!r}, got {value!r}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise EvalFailure("schema_failure", f"{path}: value {value} below minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            raise EvalFailure("schema_failure", f"{path}: value {value} above maximum {schema['maximum']}")

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                raise EvalFailure("schema_failure", f"{path}: missing required key {key!r}")

        properties = schema.get("properties", {})
        for key, child_schema in properties.items():
            if key in value:
                validate_schema(value[key], child_schema, f"{path}.{key}")

        extra = sorted(set(value.keys()) - set(properties.keys()))
        additional_properties = schema.get("additionalProperties", True)
        if additional_properties is False and extra:
            raise EvalFailure("schema_failure", f"{path}: unexpected keys {extra!r}")
        if isinstance(additional_properties, dict):
            for key in extra:
                validate_schema(value[key], additional_properties, f"{path}.{key}")

    if isinstance(value, list):
        child_schema = schema.get("items")
        if child_schema is not None:
            for index, item in enumerate(value):
                validate_schema(item, child_schema, f"{path}[{index}]")


def matches_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise EvalFailure("schema_failure", f"unsupported schema type {expected!r}")


def assert_subset(actual: Any, expected: Any, path: str = "$") -> None:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            raise EvalFailure("expectation_failure", f"{path}: expected object-like subset")
        for key, value in expected.items():
            if key not in actual:
                raise EvalFailure("expectation_failure", f"{path}: missing expected key {key!r}")
            assert_subset(actual[key], value, f"{path}.{key}")
        return

    if isinstance(expected, list):
        if not isinstance(actual, list):
            raise EvalFailure("expectation_failure", f"{path}: expected list-like subset")
        if len(actual) != len(expected):
            raise EvalFailure("expectation_failure", f"{path}: expected list length {len(expected)}, got {len(actual)}")
        for index, item in enumerate(expected):
            assert_subset(actual[index], item, f"{path}[{index}]")
        return

    if actual != expected:
        raise EvalFailure("expectation_failure", f"{path}: expected {expected!r}, got {actual!r}")


def load_schedule_config() -> dict[str, Any]:
    return load_json(SCHEDULE_CONFIG_PATH)


def check_blocks_within_workday(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    schedule = context["schedule_config"]
    work_start = parse_hhmm(schedule["workday"]["start"])
    work_end = parse_hhmm(schedule["workday"]["end"])
    for block in actual["blocks"]:
        start = parse_hhmm(block["start"])
        end = parse_hhmm(block["end"])
        if end <= start:
            raise EvalFailure("invariant_failure", f"block {block['label']!r} ends before it starts")
        if start < work_start or end > work_end:
            raise EvalFailure("invariant_failure", f"block {block['label']!r} falls outside configured workday")


def check_no_constraint_overlap(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    constraints = [block for block in actual["blocks"] if block["is_constraint"]]
    work_blocks = [block for block in actual["blocks"] if not block["is_constraint"]]
    for block in work_blocks:
        start = parse_hhmm(block["start"])
        end = parse_hhmm(block["end"])
        for constraint in constraints:
            constraint_start = parse_hhmm(constraint["start"])
            constraint_end = parse_hhmm(constraint["end"])
            overlap = min(end, constraint_end) - max(start, constraint_start)
            if overlap > 0:
                raise EvalFailure("invariant_failure", f"block {block['label']!r} overlaps constraint {constraint['label']!r}")


def check_total_hours_match(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    total = sum(block["hours"] for block in actual["blocks"])
    if not nearly_equal(total, actual["total_hours"]):
        raise EvalFailure("invariant_failure", f"block sum {total} does not match total_hours {actual['total_hours']}")


def check_project_keys_known_or_null(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    valid_keys = set(context["schedule_config"]["projects"].keys())
    for block in actual["blocks"]:
        project_key = block["project_key"]
        if project_key is not None and project_key not in valid_keys:
            raise EvalFailure("invariant_failure", f"unknown project_key {project_key!r}")


def check_no_provider_fields_before_push(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    forbidden = {"project_id", "workspace_id", "provider_payload"}
    for block in actual["blocks"]:
        extra = forbidden.intersection(block.keys())
        if extra:
            raise EvalFailure("invariant_failure", f"proposal leaked provider fields {sorted(extra)!r}")


def check_clarification_requires_empty_blocks(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    if actual["needs_clarification"]:
        if actual["blocks"]:
            raise EvalFailure("invariant_failure", "needs_clarification proposals must have empty blocks")
        if not actual["clarification_questions"]:
            raise EvalFailure("invariant_failure", "needs_clarification proposals must include questions")


def check_expected_project_keys_present(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    expected_keys = set(fixture.get("expected_project_keys", []))
    actual_keys = {
        block["project_key"]
        for block in actual["blocks"]
        if not block["is_constraint"] and block["project_key"] is not None
    }
    missing = sorted(expected_keys - actual_keys)
    if missing:
        raise EvalFailure("invariant_failure", f"missing expected project keys {missing!r}")


def check_all_nonconstraint_projectless(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    for block in actual["blocks"]:
        if not block["is_constraint"] and block["project_key"] is not None:
            raise EvalFailure("invariant_failure", f"expected projectless work block, got {block['project_key']!r}")


def check_proposal_total_hours_at_most(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    maximum = fixture["max_total_hours"]
    if actual["total_hours"] > maximum:
        raise EvalFailure("invariant_failure", f"proposal total_hours {actual['total_hours']} exceeds max {maximum}")


def check_rejection_reason_present(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    if actual["outcome"] == "reject" and not actual["rejection_reason"]:
        raise EvalFailure("invariant_failure", "reject outcome must include a rejection_reason")


def check_provider_payload_schema(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    payload = context.get("provider_payload")
    if payload is None:
        raise EvalFailure("tool_or_runtime_failure", "provider payload capture missing")
    schema = load_json(SCHEMAS_ROOT / "provider_payload.schema.json")
    validate_schema(payload, schema)


def check_provider_summary_matches_entries(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    payload = context["provider_payload"]
    entries = payload["entries"]
    summary = payload["summary"]
    total_hours = sum(entry["hours"] for entry in entries)
    total_days = len({entry["date"] for entry in entries})
    if not nearly_equal(summary["total_hours"], total_hours):
        raise EvalFailure("invariant_failure", "provider summary total_hours does not match entry sum")
    if summary["total_days"] != total_days:
        raise EvalFailure("invariant_failure", "provider summary total_days does not match unique entry dates")


def check_no_constraints_in_payload(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    payload = context["provider_payload"]
    source_blocks = context["source_proposal"]["blocks"]
    constraint_descriptions = {block["description"] for block in source_blocks if block["is_constraint"]}
    for entry in payload["entries"]:
        if entry["description"] in constraint_descriptions:
            raise EvalFailure("invariant_failure", "constraint block leaked into provider payload")


def check_project_ids_mapped_or_null(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    payload = context["provider_payload"]
    mapping = {key: project["clockify_project_id"] for key, project in context["schedule_config"]["projects"].items()}
    source_blocks = [
        block for block in context["source_proposal"]["blocks"]
        if not block["is_constraint"] and block["hours"] > 0
    ]
    for source_block, payload_entry in zip(source_blocks, payload["entries"]):
        expected = mapping.get(source_block["project_key"])
        if payload_entry["project_id"] != expected:
            raise EvalFailure(
                "invariant_failure",
                f"entry {payload_entry['description']!r} expected project_id {expected!r}, got {payload_entry['project_id']!r}",
            )


def check_no_project_key_leak(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    if "project_key" in json.dumps(context["provider_payload"]):
        raise EvalFailure("invariant_failure", "provider payload leaked project_key")


def check_per_project_budgets_known_or_empty(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    budgets = actual["per_project_budgets"]
    valid_keys = set(context["schedule_config"]["projects"].keys())
    for key, value in budgets.items():
        if key not in valid_keys:
            raise EvalFailure("invariant_failure", f"unknown budget project key {key!r}")
        if value < 0:
            raise EvalFailure("invariant_failure", f"negative budget for project {key!r}")


def check_shortfall_hours_non_negative(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    if actual["shortfall_hours"] < 0:
        raise EvalFailure("invariant_failure", f"shortfall_hours must be non-negative, got {actual['shortfall_hours']}")


def check_explicit_budget_totals_respected(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    budgets = fixture.get("expected_budgets", actual["per_project_budgets"])
    totals = {
        key: 0.0 for key in budgets
    }
    for block in actual["blocks"]:
        key = block["project_key"]
        if key in totals:
            totals[key] += block["hours"]
    for key, expected in budgets.items():
        if not nearly_equal(totals.get(key, 0.0), expected, epsilon=0.05):
            raise EvalFailure("invariant_failure", f"project {key!r} total {totals.get(key, 0.0)} does not match explicit budget {expected}")


CHECKS = {
    "blocks_within_workday": check_blocks_within_workday,
    "no_constraint_overlap": check_no_constraint_overlap,
    "total_hours_match": check_total_hours_match,
    "project_keys_known_or_null": check_project_keys_known_or_null,
    "no_provider_fields_before_push": check_no_provider_fields_before_push,
    "clarification_requires_empty_blocks": check_clarification_requires_empty_blocks,
    "expected_project_keys_present": check_expected_project_keys_present,
    "all_nonconstraint_projectless": check_all_nonconstraint_projectless,
    "proposal_total_hours_at_most": check_proposal_total_hours_at_most,
    "rejection_reason_present": check_rejection_reason_present,
    "provider_payload_schema": check_provider_payload_schema,
    "provider_summary_matches_entries": check_provider_summary_matches_entries,
    "no_constraints_in_payload": check_no_constraints_in_payload,
    "project_ids_mapped_or_null": check_project_ids_mapped_or_null,
    "no_project_key_leak": check_no_project_key_leak,
    "per_project_budgets_known_or_empty": check_per_project_budgets_known_or_empty,
    "shortfall_hours_non_negative": check_shortfall_hours_non_negative,
    "explicit_budget_totals_respected": check_explicit_budget_totals_respected,
}


def has_bare_mode_auth() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def check_logged_in_status() -> tuple[bool, str]:
    completed = subprocess.run(
        ["claude", "auth", "status"],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )
    combined = (completed.stdout or "") + (completed.stderr or "")
    if not combined.strip():
        return False, "Unable to determine Claude Code auth status."
    try:
        status = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return False, f"Unexpected Claude auth status output:\n{combined.strip()}"
    if status.get("loggedIn"):
        return True, f"Claude Code auth detected via {status.get('authMethod', 'unknown')}."
    return False, "Claude Code is not logged in. Run `claude auth login` first."


def auth_preflight(bare_mode: bool) -> tuple[bool, str]:
    if bare_mode:
        if has_bare_mode_auth():
            return True, "Bare mode auth detected via ANTHROPIC_API_KEY."
        return False, (
            "Bare mode requires ANTHROPIC_API_KEY. "
            "Unset `--bare-mode` for normal local runs, or export ANTHROPIC_API_KEY for headless runs."
        )
    return check_logged_in_status()


def build_prompt(payload: dict[str, Any]) -> str:
    return (
        "Return only valid JSON.\n"
        "Use this input JSON exactly as the runtime payload:\n\n"
        f"{json.dumps(payload, indent=2)}\n"
    )


def usage_from_wrapper(wrapper: dict[str, Any] | None) -> UsageStats:
    if wrapper is None:
        return UsageStats()
    usage = wrapper.get("usage", {})
    return UsageStats(
        input_tokens=int(usage.get("input_tokens", 0) or 0),
        output_tokens=int(usage.get("output_tokens", 0) or 0),
        cost_usd=float(wrapper.get("total_cost_usd", 0.0) or 0.0),
        duration_ms=int(wrapper.get("duration_ms", 0) or 0),
    )


def excerpt(text: str, limit: int = 280) -> str:
    stripped = text.strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[:limit] + "..."


def build_command(agent: str, inline_agents: str, bare_mode: bool, extra_dirs: list[str]) -> list[str]:
    command = [
        "claude",
        "-p",
        "--output-format",
        "json",
        "--no-session-persistence",
        "--agents",
        inline_agents,
        "--agent",
        agent,
    ]
    if bare_mode:
        command.insert(2, "--bare")
    if extra_dirs:
        command.extend(["--add-dir", *extra_dirs])
    return command


def run_claude_agent(
    agent: str,
    payload: dict[str, Any],
    artifact_dir: Path,
    options: RunOptions,
    extra_dirs: list[str] | None = None,
) -> ClaudeInvocation:
    extra_dirs = extra_dirs or []
    inline_agents = json.dumps(build_inline_agent(agent))
    prompt = build_prompt(payload)
    save_text(artifact_dir / "prompt.txt", prompt)

    command = build_command(agent, inline_agents, options.bare_mode, extra_dirs)
    save_text(artifact_dir / "command.txt", " ".join(command))

    completed = subprocess.run(
        command,
        cwd=str(ROOT),
        input=prompt,
        text=True,
        capture_output=True,
    )

    save_text(artifact_dir / "stdout.txt", completed.stdout)
    save_text(artifact_dir / "stderr.txt", completed.stderr)

    wrapper: dict[str, Any] | None = None
    if completed.stdout.strip():
        try:
            wrapper = json.loads(completed.stdout)
            save_json(artifact_dir / "raw_result.json", wrapper)
        except json.JSONDecodeError:
            save_text(artifact_dir / "raw_result.invalid.txt", completed.stdout)

    usage = usage_from_wrapper(wrapper)
    result_text = ""
    if wrapper is not None:
        result_text = str(wrapper.get("result", "") or "")
        if wrapper.get("is_error"):
            if "Not logged in" in result_text:
                raise EvalFailure("auth_failure", "Claude Code is not logged in", excerpt(result_text))
            raise EvalFailure(
                "tool_or_runtime_failure",
                "Claude returned an error wrapper result.",
                excerpt(result_text or completed.stderr or completed.stdout),
            )

    if completed.returncode != 0:
        if wrapper is not None and "Not logged in" in result_text:
            raise EvalFailure("auth_failure", "Claude Code is not logged in", excerpt(result_text))
        raise EvalFailure(
            "tool_or_runtime_failure",
            f"claude exited with code {completed.returncode}",
            excerpt(result_text or completed.stderr or completed.stdout),
        )

    payload_value, extraction_warning = extract_payload_text(result_text, options.strict_output)

    for marker in TOOL_RUNTIME_PATTERNS:
        if marker in result_text.lower():
            raise EvalFailure(
                "tool_or_runtime_failure",
                "Subagent reported a tool or sandbox execution problem.",
                excerpt(result_text),
            )

    save_json(artifact_dir / "extracted_payload.json", payload_value)
    if extraction_warning:
        save_text(artifact_dir / "output_warning.txt", extraction_warning)

    return ClaudeInvocation(
        payload=payload_value,
        wrapper=wrapper,
        raw_stdout=completed.stdout,
        raw_stderr=completed.stderr,
        result_text=result_text,
        extraction_warning=extraction_warning,
        usage=usage,
        command=command,
    )


def load_schema_for_agent(agent: str) -> dict[str, Any]:
    return load_json(SCHEMAS_ROOT / SCHEMA_BY_AGENT[agent])


def build_reconstructor_payload(narrative_input: dict[str, Any]) -> dict[str, Any]:
    return {
        "narrative_input": narrative_input,
        "schedule_config_path": str(SCHEDULE_CONFIG_PATH),
    }


def build_push_mock_project() -> tuple[Path, Path, Path]:
    temp_root = Path(tempfile.mkdtemp(prefix="clockify-push-eval-"))
    config_dir = temp_root / "skill" / "config"
    scripts_dir = temp_root / "skill" / "scripts"
    config_dir.mkdir(parents=True)
    scripts_dir.mkdir(parents=True)
    shutil.copy2(SCHEDULE_CONFIG_PATH, config_dir / "schedule_defaults.json")

    push_script = """#!/usr/bin/env python3
import json
import sys
from pathlib import Path

payload_path = Path(sys.argv[1])
capture_path = Path(__file__).with_name("push_capture.json")
data = json.loads(payload_path.read_text())
capture_path.write_text(json.dumps(data, indent=2))
print(json.dumps({
    "total_processed": len(data["entries"]),
    "successful": len(data["entries"]),
    "failed": 0,
    "failed_entries": []
}))
"""

    timesheet_script = """#!/usr/bin/env python3
import json
import sys
from pathlib import Path

payload_path = Path(sys.argv[1])
capture_path = Path(__file__).with_name("timesheet_capture.json")
data = json.loads(payload_path.read_text())
capture_path.write_text(json.dumps(data, indent=2))
output_path = Path(sys.argv[2]).expanduser()
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text("mock timesheet")
print(json.dumps({
    "status": "ok",
    "format": "csv",
    "output": str(output_path),
    "total_hours": sum(entry.get("hours", 0) for entry in data.get("entries", [])),
    "total_days": len({entry["date"] for entry in data.get("entries", [])})
}))
"""

    for path, content in {
        scripts_dir / "push_clockify.py": push_script,
        scripts_dir / "generate_timesheet.py": timesheet_script,
    }.items():
        path.write_text(content)
        path.chmod(0o755)

    return temp_root, scripts_dir / "push_capture.json", scripts_dir / "timesheet_capture.json"


def fixture_context() -> dict[str, Any]:
    return {
        "schedule_config": load_schedule_config(),
        "provider_payload": None,
        "source_proposal": None,
    }


def write_failure_report(artifact_dir: Path, category: str, message: str, excerpt_text: str | None) -> None:
    report = {
        "category": category,
        "message": message,
        "excerpt": excerpt_text,
    }
    save_json(artifact_dir / "failure_report.json", report)


def run_single_fixture(fixture: dict[str, Any], artifact_dir: Path, options: RunOptions) -> tuple[UsageStats, list[str]]:
    agent = fixture["agent"]
    context = fixture_context()
    extra_dirs: list[str] = []

    if agent == "ct-parser":
        payload = fixture["input"]
    elif agent == "ct-reconstructor":
        payload = build_reconstructor_payload(fixture["input"]["narrative_input"])
    elif agent == "ct-validator":
        payload = fixture["input"]
    elif agent == "ct-push":
        temp_root, capture_path, timesheet_capture_path = build_push_mock_project()
        context["source_proposal"] = fixture["input"]["proposal"]
        payload = {"proposal": context["source_proposal"], "project_root": str(temp_root)}
        extra_dirs = [str(temp_root), "/tmp"]
    else:
        raise EvalFailure("expectation_failure", f"unsupported agent {agent!r}")

    invocation = run_claude_agent(agent, payload, artifact_dir, options, extra_dirs=extra_dirs)
    actual = invocation.payload
    validate_schema(actual, load_schema_for_agent(agent))

    warnings: list[str] = []
    if invocation.extraction_warning:
        warnings.append(invocation.extraction_warning)

    if agent == "ct-push":
        if not capture_path.exists():
            raise EvalFailure("tool_or_runtime_failure", "ct-push did not produce provider payload capture")
        context["provider_payload"] = load_json(capture_path)
        save_json(artifact_dir / "provider_payload.json", context["provider_payload"])
        if timesheet_capture_path.exists():
            save_json(artifact_dir / "timesheet_capture.json", load_json(timesheet_capture_path))

    if "expected" in fixture:
        assert_subset(actual, fixture["expected"])
    if "expected_payload" in fixture:
        assert_subset(context["provider_payload"], fixture["expected_payload"])

    for check_name in fixture.get("checks", []):
        CHECKS[check_name](actual, fixture, context)

    return invocation.usage, warnings


def run_chain_fixture(fixture: dict[str, Any], artifact_dir: Path, options: RunOptions) -> tuple[UsageStats, list[str]]:
    total_usage = UsageStats()
    warnings: list[str] = []
    previous_output: Any = None
    schedule_context = fixture_context()

    for index, step in enumerate(fixture["steps"], start=1):
        step_dir = artifact_dir / f"step-{index:02d}-{step['agent']}"
        step_dir.mkdir(parents=True, exist_ok=True)
        agent = step["agent"]
        extra_dirs: list[str] = []
        local_context = dict(schedule_context)

        if "input" in step:
            if agent == "ct-reconstructor":
                payload = build_reconstructor_payload(step["input"]["narrative_input"])
            elif agent == "ct-push":
                temp_root, capture_path, timesheet_capture_path = build_push_mock_project()
                local_context["source_proposal"] = step["input"]["proposal"]
                payload = {"proposal": local_context["source_proposal"], "project_root": str(temp_root)}
                extra_dirs = [str(temp_root), "/tmp"]
            else:
                payload = step["input"]
        else:
            if step["input_from"] == "parser_first":
                if not isinstance(previous_output, list) or not previous_output:
                    raise EvalFailure("expectation_failure", "parser_first requires a non-empty parser output")
                payload = build_reconstructor_payload(previous_output[0])
            elif step["input_from"] == "previous":
                payload = previous_output
            else:
                raise EvalFailure("expectation_failure", f"unsupported chain input_from {step['input_from']!r}")

        invocation = run_claude_agent(agent, payload, step_dir, options, extra_dirs=extra_dirs)
        actual = invocation.payload
        validate_schema(actual, load_schema_for_agent(agent))
        previous_output = actual
        total_usage.input_tokens += invocation.usage.input_tokens
        total_usage.output_tokens += invocation.usage.output_tokens
        total_usage.cost_usd += invocation.usage.cost_usd
        total_usage.duration_ms += invocation.usage.duration_ms

        if invocation.extraction_warning:
            warnings.append(f"{agent}: {invocation.extraction_warning}")

        if agent == "ct-push":
            if not capture_path.exists():
                raise EvalFailure("tool_or_runtime_failure", "ct-push did not produce provider payload capture")
            local_context["provider_payload"] = load_json(capture_path)
            save_json(step_dir / "provider_payload.json", local_context["provider_payload"])
            if timesheet_capture_path.exists():
                save_json(step_dir / "timesheet_capture.json", load_json(timesheet_capture_path))

        if "expected" in step:
            assert_subset(actual, step["expected"])
        if "allowed_outcomes" in step and actual.get("outcome") not in step["allowed_outcomes"]:
            raise EvalFailure(
                "expectation_failure",
                f"step {agent} outcome {actual.get('outcome')!r} not in {step['allowed_outcomes']!r}",
            )

        for check_name in step.get("checks", []):
            CHECKS[check_name](actual, step, local_context)

    return total_usage, warnings


def discover_fixture_paths(match: str | None) -> list[Path]:
    fixtures = sorted(FIXTURES_ROOT.rglob("*.json"))
    if match:
        filtered: list[Path] = []
        for path in fixtures:
            fixture = load_json(path)
            if match in str(path) or match in fixture.get("name", ""):
                filtered.append(path)
        fixtures = filtered
    return fixtures


def self_check(match: str | None) -> int:
    errors: list[str] = []
    fixture_names: set[str] = set()

    for path in discover_fixture_paths(match):
        fixture = load_json(path)
        if fixture["name"] in fixture_names:
            errors.append(f"duplicate fixture name {fixture['name']!r}")
        fixture_names.add(fixture["name"])
        if path.parent.name == "chains":
            for step in fixture["steps"]:
                if step["agent"] not in SCHEMA_BY_AGENT:
                    errors.append(f"{fixture['name']}: unknown agent {step['agent']!r}")
                for check_name in step.get("checks", []):
                    if check_name not in CHECKS:
                        errors.append(f"{fixture['name']}: unknown check {check_name!r}")
        else:
            if fixture["agent"] not in SCHEMA_BY_AGENT:
                errors.append(f"{fixture['name']}: unknown agent {fixture['agent']!r}")
            for check_name in fixture.get("checks", []):
                if check_name not in CHECKS:
                    errors.append(f"{fixture['name']}: unknown check {check_name!r}")

    for schema_name in SCHEMA_BY_AGENT.values():
        schema_path = SCHEMAS_ROOT / schema_name
        if not schema_path.exists():
            errors.append(f"missing schema {schema_name}")
        else:
            load_json(schema_path)

    extraction_tests = [
        ('{"ok":true}', False, True),
        ("```json\n{\"ok\":true}\n```", False, True),
        ("Here is the result:\n\n```json\n{\"ok\":true}\n```", False, True),
        ("Here is the result:\n\n```json\n{\"ok\":true}\n```", True, False),
        ("not json at all", False, False),
    ]
    for sample, strict_output, should_pass in extraction_tests:
        try:
            extract_payload_text(sample, strict_output)
            passed = True
        except EvalFailure:
            passed = False
        if passed != should_pass:
            errors.append(f"json extraction self-check failed for sample {sample!r} strict={strict_output}")

    temp_root, capture_path, _ = build_push_mock_project()
    if not (temp_root / "skill" / "scripts" / "push_clockify.py").exists():
        errors.append("mock push project missing push_clockify.py")
    if capture_path.exists():
        errors.append("mock push capture should not exist before execution")
    shutil.rmtree(temp_root)

    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1

    print(f"PASS fixture-count={len(discover_fixture_paths(match))}")
    return 0


def format_usage(usage: UsageStats) -> str:
    return (
        f"dur={usage.duration_ms}ms "
        f"tok={usage.input_tokens}/{usage.output_tokens} "
        f"cost=${usage.cost_usd:.6f}"
    )


def print_failure_details(result: EvalResult) -> None:
    print(f"  category: {result.category}")
    print(f"  reason:   {result.message}")
    if result.warnings:
        for warning in result.warnings:
            print(f"  warning:  {warning}")
    failure_report = result.artifact_dir / "failure_report.json"
    if failure_report.exists():
        report = load_json(failure_report)
        if report.get("excerpt"):
            print(f"  excerpt:  {report['excerpt']}")
    print(f"  artifact: {result.artifact_dir}")


def print_verbose_details(result: EvalResult) -> None:
    prompt_path = result.artifact_dir / "prompt.txt"
    stdout_path = result.artifact_dir / "stdout.txt"
    stderr_path = result.artifact_dir / "stderr.txt"
    for label, path in [("prompt", prompt_path), ("stdout", stdout_path), ("stderr", stderr_path)]:
        if path.exists():
            content = path.read_text().strip()
            if content:
                print(f"  {label}: {excerpt(content, limit=600)}")


def run_fixture(fixture_path: Path, run_root: Path, options: RunOptions) -> EvalResult:
    fixture = load_json(fixture_path)
    name = fixture["name"]
    artifact_dir = run_root / name
    artifact_dir.mkdir(parents=True, exist_ok=True)
    save_json(artifact_dir / "fixture.json", fixture)

    try:
        if fixture_path.parent.name == "chains":
            usage, warnings = run_chain_fixture(fixture, artifact_dir, options)
        else:
            usage, warnings = run_single_fixture(fixture, artifact_dir, options)
        status = "WARN" if warnings else "PASS"
        return EvalResult(name, status, None, "ok", artifact_dir, usage, warnings)
    except EvalFailure as exc:
        write_failure_report(artifact_dir, exc.category, exc.message, exc.excerpt)
        raw_result_path = artifact_dir / "raw_result.json"
        usage = UsageStats()
        if raw_result_path.exists():
            usage = usage_from_wrapper(load_json(raw_result_path))
        return EvalResult(name, "FAIL", exc.category, exc.message, artifact_dir, usage, [])


def write_run_summary(run_root: Path, results: list[EvalResult]) -> None:
    by_category: dict[str, int] = {}
    total_usage = UsageStats()
    for result in results:
        if result.category:
            by_category[result.category] = by_category.get(result.category, 0) + 1
        total_usage.input_tokens += result.usage.input_tokens
        total_usage.output_tokens += result.usage.output_tokens
        total_usage.cost_usd += result.usage.cost_usd
        total_usage.duration_ms += result.usage.duration_ms

    summary = {
        "results": [
            {
                "name": result.name,
                "status": result.status,
                "category": result.category,
                "message": result.message,
                "artifact_dir": str(result.artifact_dir),
                "warnings": result.warnings,
                "usage": {
                    "input_tokens": result.usage.input_tokens,
                    "output_tokens": result.usage.output_tokens,
                    "cost_usd": result.usage.cost_usd,
                    "duration_ms": result.usage.duration_ms,
                },
            }
            for result in results
        ],
        "summary": {
            "pass": sum(1 for result in results if result.status == "PASS"),
            "warn": sum(1 for result in results if result.status == "WARN"),
            "fail": sum(1 for result in results if result.status == "FAIL"),
            "by_category": by_category,
            "input_tokens": total_usage.input_tokens,
            "output_tokens": total_usage.output_tokens,
            "cost_usd": total_usage.cost_usd,
            "duration_ms": total_usage.duration_ms,
        },
    }
    save_json(run_root / "run_summary.json", summary)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run contract-first subagent evals.")
    parser.add_argument("--self-check", action="store_true", help="Validate fixtures and harness setup without invoking Claude")
    parser.add_argument("--match", help="Only run fixtures whose path contains this substring")
    parser.add_argument("--bare-mode", action="store_true", help="Run Claude in bare mode with ANTHROPIC_API_KEY")
    parser.add_argument("--verbose", action="store_true", help="Print prompt/stdout/stderr excerpts for every fixture")
    parser.add_argument("--show-passing-usage", action="store_true", help="Print additional usage details for passing fixtures")
    parser.add_argument("--strict-output", action="store_true", help="Fail if subagents return fenced or prose-wrapped JSON")
    parser.add_argument("--max-failures", type=int, help="Stop after this many failures")
    args = parser.parse_args()

    if args.self_check:
        return self_check(args.match)

    fixture_paths = discover_fixture_paths(args.match)
    if not fixture_paths:
        print("No fixtures matched.")
        return 0

    auth_ok, auth_message = auth_preflight(args.bare_mode)
    print(auth_message)
    if not auth_ok:
        return 1

    run_root = ARTIFACTS_ROOT / datetime.now().strftime("%Y%m%d-%H%M%S")
    run_root.mkdir(parents=True, exist_ok=True)

    options = RunOptions(
        bare_mode=args.bare_mode,
        verbose=args.verbose,
        show_passing_usage=args.show_passing_usage,
        strict_output=args.strict_output,
        max_failures=args.max_failures,
    )

    results: list[EvalResult] = []
    failure_count = 0

    for fixture_path in fixture_paths:
        result = run_fixture(fixture_path, run_root, options)
        results.append(result)
        print(f"{result.status:4} {result.name} {format_usage(result.usage)} [{result.artifact_dir}]")

        if result.status == "FAIL":
            failure_count += 1
            print_failure_details(result)
            if options.verbose:
                print_verbose_details(result)
        elif result.status == "WARN":
            for warning in result.warnings:
                print(f"  warning:  {warning}")
            if options.verbose:
                print_verbose_details(result)
        elif options.show_passing_usage:
            print(f"  usage:    input={result.usage.input_tokens} output={result.usage.output_tokens} cost=${result.usage.cost_usd:.6f}")
            if options.verbose:
                print_verbose_details(result)

        if options.max_failures is not None and failure_count >= options.max_failures:
            print(f"Reached max failures ({options.max_failures}); stopping early.")
            break

    write_run_summary(run_root, results)

    by_category: dict[str, int] = {}
    total_usage = UsageStats()
    for result in results:
        if result.category:
            by_category[result.category] = by_category.get(result.category, 0) + 1
        total_usage.input_tokens += result.usage.input_tokens
        total_usage.output_tokens += result.usage.output_tokens
        total_usage.cost_usd += result.usage.cost_usd
        total_usage.duration_ms += result.usage.duration_ms

    print("\nSummary:")
    print(
        f"  pass={sum(1 for result in results if result.status == 'PASS')} "
        f"warn={sum(1 for result in results if result.status == 'WARN')} "
        f"fail={sum(1 for result in results if result.status == 'FAIL')} "
        f"total={len(results)}"
    )
    if by_category:
        print("  failure-categories:")
        for category, count in sorted(by_category.items()):
            print(f"    {category}: {count}")
    print(
        f"  totals: dur={total_usage.duration_ms}ms "
        f"tok={total_usage.input_tokens}/{total_usage.output_tokens} "
        f"cost=${total_usage.cost_usd:.6f}"
    )
    print(f"  run-artifacts: {run_root}")

    return 1 if any(result.status == "FAIL" for result in results) else 0


if __name__ == "__main__":
    sys.exit(main())
