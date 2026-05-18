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
from dataclasses import dataclass
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


class EvalFailure(Exception):
    pass


class AuthRequired(Exception):
    pass


@dataclass
class EvalResult:
    name: str
    status: str
    message: str
    artifact_dir: Path


def load_json(path: Path) -> Any:
    with path.open() as handle:
        return json.load(handle)


def save_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def parse_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text()
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not match:
        raise EvalFailure(f"{path} does not contain YAML frontmatter")

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
            if not value:
                data[key] = []
            else:
                data[key] = [tool.strip() for tool in value.split(",")]
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


def strip_json_output(text: str) -> Any:
    stripped = text.strip()
    if not stripped:
        raise EvalFailure("empty output")
    try:
        return json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise EvalFailure(f"invalid JSON output: {exc}") from exc


def validate_schema(value: Any, schema: Any, path: str = "$") -> None:
    if not isinstance(schema, dict):
        raise EvalFailure(f"unsupported schema node at {path}")

    if "type" in schema:
        expected_types = schema["type"]
        if not isinstance(expected_types, list):
            expected_types = [expected_types]
        if not any(matches_type(value, expected) for expected in expected_types):
            raise EvalFailure(f"{path}: expected {expected_types}, got {type(value).__name__}")

    if "const" in schema and value != schema["const"]:
        raise EvalFailure(f"{path}: expected const {schema['const']!r}, got {value!r}")

    if "enum" in schema and value not in schema["enum"]:
        raise EvalFailure(f"{path}: expected one of {schema['enum']!r}, got {value!r}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise EvalFailure(f"{path}: value {value} below minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            raise EvalFailure(f"{path}: value {value} above maximum {schema['maximum']}")

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                raise EvalFailure(f"{path}: missing required key {key!r}")

        properties = schema.get("properties", {})
        for key, child_schema in properties.items():
            if key in value:
                validate_schema(value[key], child_schema, f"{path}.{key}")

        if schema.get("additionalProperties") is False:
            extra = sorted(set(value.keys()) - set(properties.keys()))
            if extra:
                raise EvalFailure(f"{path}: unexpected keys {extra!r}")

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
    raise EvalFailure(f"unsupported schema type {expected!r}")


def assert_subset(actual: Any, expected: Any, path: str = "$") -> None:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            raise EvalFailure(f"{path}: expected object-like subset")
        for key, value in expected.items():
            if key not in actual:
                raise EvalFailure(f"{path}: missing expected key {key!r}")
            assert_subset(actual[key], value, f"{path}.{key}")
        return

    if isinstance(expected, list):
        if not isinstance(actual, list):
            raise EvalFailure(f"{path}: expected list-like subset")
        if len(actual) != len(expected):
            raise EvalFailure(f"{path}: expected list length {len(expected)}, got {len(actual)}")
        for index, item in enumerate(expected):
            assert_subset(actual[index], item, f"{path}[{index}]")
        return

    if actual != expected:
        raise EvalFailure(f"{path}: expected {expected!r}, got {actual!r}")


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
            raise EvalFailure(f"block {block['label']!r} ends before it starts")
        if start < work_start or end > work_end:
            raise EvalFailure(f"block {block['label']!r} falls outside configured workday")


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
                raise EvalFailure(
                    f"block {block['label']!r} overlaps constraint {constraint['label']!r}"
                )


def check_total_hours_match(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    total = sum(block["hours"] for block in actual["blocks"])
    if not nearly_equal(total, actual["total_hours"]):
        raise EvalFailure(f"block sum {total} does not match total_hours {actual['total_hours']}")


def check_project_keys_known_or_null(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    valid_keys = set(context["schedule_config"]["projects"].keys())
    for block in actual["blocks"]:
        project_key = block["project_key"]
        if project_key is not None and project_key not in valid_keys:
            raise EvalFailure(f"unknown project_key {project_key!r}")


def check_no_provider_fields_before_push(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    forbidden = {"project_id", "workspace_id", "provider_payload"}
    for block in actual["blocks"]:
        extra = forbidden.intersection(block.keys())
        if extra:
            raise EvalFailure(f"proposal leaked provider fields {sorted(extra)!r}")


def check_clarification_requires_empty_blocks(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    if actual["needs_clarification"]:
        if actual["blocks"]:
            raise EvalFailure("needs_clarification proposals must have empty blocks")
        if not actual["clarification_questions"]:
            raise EvalFailure("needs_clarification proposals must include questions")


def check_expected_project_keys_present(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    expected_keys = set(fixture.get("expected_project_keys", []))
    actual_keys = {
        block["project_key"]
        for block in actual["blocks"]
        if not block["is_constraint"] and block["project_key"] is not None
    }
    missing = sorted(expected_keys - actual_keys)
    if missing:
        raise EvalFailure(f"missing expected project keys {missing!r}")


def check_all_nonconstraint_projectless(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    for block in actual["blocks"]:
        if not block["is_constraint"] and block["project_key"] is not None:
            raise EvalFailure(f"expected projectless work block, got {block['project_key']!r}")


def check_proposal_total_hours_at_most(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    maximum = fixture["max_total_hours"]
    if actual["total_hours"] > maximum:
        raise EvalFailure(f"proposal total_hours {actual['total_hours']} exceeds max {maximum}")


def check_rejection_reason_present(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    if actual["outcome"] == "reject" and not actual["rejection_reason"]:
        raise EvalFailure("reject outcome must include a rejection_reason")


def check_provider_payload_schema(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    payload = context.get("provider_payload")
    if payload is None:
        raise EvalFailure("provider payload capture missing")
    schema = load_json(SCHEMAS_ROOT / "provider_payload.schema.json")
    validate_schema(payload, schema)


def check_provider_summary_matches_entries(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    payload = context["provider_payload"]
    entries = payload["entries"]
    summary = payload["summary"]
    total_hours = sum(entry["hours"] for entry in entries)
    total_days = len({entry["date"] for entry in entries})
    if not nearly_equal(summary["total_hours"], total_hours):
        raise EvalFailure("provider summary total_hours does not match entry sum")
    if summary["total_days"] != total_days:
        raise EvalFailure("provider summary total_days does not match unique entry dates")


def check_no_constraints_in_payload(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    payload = context["provider_payload"]
    source_blocks = context["source_proposal"]["blocks"]
    constraint_descriptions = {
        block["description"] for block in source_blocks if block["is_constraint"]
    }
    for entry in payload["entries"]:
        if entry["description"] in constraint_descriptions:
            raise EvalFailure("constraint block leaked into provider payload")


def check_project_ids_mapped_or_null(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    payload = context["provider_payload"]
    mapping = {
        key: project["clockify_project_id"]
        for key, project in context["schedule_config"]["projects"].items()
    }

    for source_block, payload_entry in zip(
        [block for block in context["source_proposal"]["blocks"] if not block["is_constraint"] and block["hours"] > 0],
        payload["entries"],
    ):
        expected = mapping.get(source_block["project_key"])
        if payload_entry["project_id"] != expected:
            raise EvalFailure(
                f"entry {payload_entry['description']!r} expected project_id {expected!r}, got {payload_entry['project_id']!r}"
            )


def check_no_project_key_leak(actual: dict[str, Any], fixture: dict[str, Any], context: dict[str, Any]) -> None:
    payload_text = json.dumps(context["provider_payload"])
    if "project_key" in payload_text:
        raise EvalFailure("provider payload leaked project_key")


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
}


def artifact_dir_for(name: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return ARTIFACTS_ROOT / timestamp / name


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

    logged_in = bool(status.get("loggedIn"))
    method = status.get("authMethod", "unknown")
    if logged_in:
        return True, f"Claude Code auth detected via {method}."

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


def build_prompt(agent: str, payload: dict[str, Any]) -> str:
    return (
        "Return only valid JSON.\n"
        "Use this input JSON exactly as the runtime payload:\n\n"
        f"{json.dumps(payload, indent=2)}\n"
    )


def run_claude_agent(agent: str, payload: dict[str, Any], artifact_dir: Path, bare_mode: bool) -> Any:
    inline_agents = json.dumps(build_inline_agent(agent))
    prompt = build_prompt(agent, payload)
    save_text(artifact_dir / "prompt.txt", prompt)

    command = [
        "claude",
        "-p",
        "--no-session-persistence",
        "--agents",
        inline_agents,
        "--agent",
        agent,
    ]
    if bare_mode:
        command.insert(2, "--bare")

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

    if completed.returncode != 0:
        combined = f"{completed.stdout}\n{completed.stderr}"
        if "Not logged in" in combined:
            raise AuthRequired("Claude Code is not logged in")
        raise EvalFailure(f"claude exited with code {completed.returncode}")

    return strip_json_output(completed.stdout)


def load_schema_for_agent(agent: str) -> dict[str, Any]:
    return load_json(SCHEMAS_ROOT / SCHEMA_BY_AGENT[agent])


def build_reconstructor_payload(narrative_input: dict[str, Any]) -> dict[str, Any]:
    return {
        "narrative_input": narrative_input,
        "schedule_config_path": str(SCHEDULE_CONFIG_PATH),
    }


def build_push_mock_project() -> tuple[Path, Path]:
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
print(json.dumps({
    "status": "ok",
    "format": "csv",
    "output": sys.argv[2],
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

    return temp_root, scripts_dir / "push_capture.json"


def run_fixture(fixture_path: Path, auth_blocked: bool, bare_mode: bool) -> tuple[EvalResult, bool]:
    fixture = load_json(fixture_path)
    name = fixture["name"]
    artifact_dir = artifact_dir_for(name)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    save_text(artifact_dir / "fixture.json", json.dumps(fixture, indent=2))

    if auth_blocked:
        return EvalResult(name, "SKIP", "Auth preflight failed", artifact_dir), True

    try:
        if fixture_path.parent.name == "chains":
            run_chain_fixture(fixture, artifact_dir, bare_mode)
        else:
            run_single_fixture(fixture, artifact_dir, bare_mode)
        return EvalResult(name, "PASS", "ok", artifact_dir), False
    except AuthRequired as exc:
        return EvalResult(name, "SKIP", str(exc), artifact_dir), True
    except EvalFailure as exc:
        return EvalResult(name, "FAIL", str(exc), artifact_dir), False


def run_single_fixture(fixture: dict[str, Any], artifact_dir: Path, bare_mode: bool) -> None:
    agent = fixture["agent"]
    schedule_config = load_schedule_config()
    source_proposal = None
    provider_payload = None

    if agent == "ct-parser":
        payload = fixture["input"]
    elif agent == "ct-reconstructor":
        payload = build_reconstructor_payload(fixture["input"]["narrative_input"])
    elif agent == "ct-validator":
        payload = fixture["input"]
    elif agent == "ct-push":
        temp_root, capture_path = build_push_mock_project()
        source_proposal = fixture["input"]["proposal"]
        payload = {
            "proposal": source_proposal,
            "project_root": str(temp_root),
        }
    else:
        raise EvalFailure(f"unsupported agent {agent!r}")

    actual = run_claude_agent(agent, payload, artifact_dir, bare_mode)
    save_text(artifact_dir / "actual.json", json.dumps(actual, indent=2))

    validate_schema(actual, load_schema_for_agent(agent))

    if agent == "ct-push":
        provider_payload = load_json(capture_path)
        save_text(artifact_dir / "provider_payload.json", json.dumps(provider_payload, indent=2))

    if "expected" in fixture:
        assert_subset(actual, fixture["expected"])

    if "expected_payload" in fixture:
        assert_subset(provider_payload, fixture["expected_payload"])

    context = {
        "schedule_config": schedule_config,
        "provider_payload": provider_payload,
        "source_proposal": source_proposal,
    }

    for check_name in fixture.get("checks", []):
        CHECKS[check_name](actual, fixture, context)


def run_chain_fixture(fixture: dict[str, Any], artifact_dir: Path, bare_mode: bool) -> None:
    previous_output: Any = None
    schedule_config = load_schedule_config()

    for index, step in enumerate(fixture["steps"], start=1):
        step_dir = artifact_dir / f"step-{index:02d}-{step['agent']}"
        step_dir.mkdir(parents=True, exist_ok=True)
        agent = step["agent"]
        source_proposal = None
        provider_payload = None

        if "input" in step:
            if agent == "ct-reconstructor":
                payload = build_reconstructor_payload(step["input"]["narrative_input"])
            elif agent == "ct-push":
                temp_root, capture_path = build_push_mock_project()
                source_proposal = step["input"]["proposal"]
                payload = {"proposal": source_proposal, "project_root": str(temp_root)}
            else:
                payload = step["input"]
        else:
            input_from = step["input_from"]
            if input_from == "parser_first":
                if not isinstance(previous_output, list) or not previous_output:
                    raise EvalFailure("parser_first requires a non-empty parser output")
                payload = build_reconstructor_payload(previous_output[0])
            elif input_from == "previous":
                payload = previous_output
            else:
                raise EvalFailure(f"unsupported chain input_from {input_from!r}")

        actual = run_claude_agent(agent, payload, step_dir, bare_mode)
        save_text(step_dir / "actual.json", json.dumps(actual, indent=2))
        validate_schema(actual, load_schema_for_agent(agent))

        if agent == "ct-push":
            provider_payload = load_json(capture_path)
            save_text(step_dir / "provider_payload.json", json.dumps(provider_payload, indent=2))

        if "expected" in step:
            assert_subset(actual, step["expected"])

        if "allowed_outcomes" in step:
            if actual.get("outcome") not in step["allowed_outcomes"]:
                raise EvalFailure(
                    f"step {agent} outcome {actual.get('outcome')!r} not in {step['allowed_outcomes']!r}"
                )

        context = {
            "schedule_config": schedule_config,
            "provider_payload": provider_payload,
            "source_proposal": source_proposal,
        }
        for check_name in step.get("checks", []):
            CHECKS[check_name](actual, step, context)

        previous_output = actual


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

    temp_root, capture_path = build_push_mock_project()
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Run contract-first subagent evals.")
    parser.add_argument("--self-check", action="store_true", help="Validate fixtures and harness setup without invoking Claude")
    parser.add_argument("--match", help="Only run fixtures whose path contains this substring")
    parser.add_argument(
        "--bare-mode",
        action="store_true",
        help="Run Claude in bare mode. Requires ANTHROPIC_API_KEY and skips stored Claude login credentials.",
    )
    args = parser.parse_args()

    if args.self_check:
        return self_check(args.match)

    auth_blocked = False
    results: list[EvalResult] = []

    fixture_paths = discover_fixture_paths(args.match)
    if not fixture_paths:
        print("No fixtures matched.")
        return 0

    auth_ok, auth_message = auth_preflight(args.bare_mode)
    print(auth_message)
    auth_blocked = not auth_ok

    for fixture_path in fixture_paths:
        result, auth_blocked = run_fixture(fixture_path, auth_blocked, args.bare_mode)
        results.append(result)
        print(f"{result.status:4} {result.name} -> {result.message} [{result.artifact_dir}]")

    failed = [result for result in results if result.status == "FAIL"]
    skipped = [result for result in results if result.status == "SKIP"]
    passed = [result for result in results if result.status == "PASS"]

    print(
        f"\nSummary: pass={len(passed)} fail={len(failed)} skip={len(skipped)} total={len(results)}"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
