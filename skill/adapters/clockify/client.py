"""Thin wrapper over scripts/push_clockify.py for use by the adapter layer."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

_SCRIPT = Path(__file__).parent.parent.parent / "scripts" / "push_clockify.py"


def push(payload_dict: dict, dry_run: bool = False) -> dict:
    """Write payload to a temp file and invoke push_clockify.py. Returns the result dict."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as tmp:
        json.dump(payload_dict, tmp)
        tmp_path = tmp.name

    cmd = [sys.executable, str(_SCRIPT), tmp_path]
    if dry_run:
        cmd.append("--dry-run")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"push_clockify.py exited with code {result.returncode}:\n{result.stderr}"
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"raw_output": result.stdout}
