#!/usr/bin/env python3
"""Validate Clockify credentials without exposing them.

Checks:
1. credentials.json exists at ~/.config/clockify/
2. Required fields are present and non-empty
3. API key is valid (test call to /user endpoint)
4. Workspace ID is valid

Outputs JSON status — never prints the actual key values.
"""

import json
import sys
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

CRED_PATH = os.path.expanduser("~/.config/clockify/credentials.json")
API_BASE = "https://api.clockify.me/api/v1"

def main():
    # Check file exists
    if not os.path.exists(CRED_PATH):
        print(json.dumps({
            "status": "error",
            "step": "file_check",
            "message": f"Credentials file not found at {CRED_PATH}",
            "fix": "Create the file with: mkdir -p ~/.config/clockify && cat > ~/.config/clockify/credentials.json"
        }, indent=2))
        sys.exit(1)

    # Check permissions
    file_mode = oct(os.stat(CRED_PATH).st_mode)[-3:]
    if file_mode not in ("600", "400"):
        print(json.dumps({
            "status": "warning",
            "step": "permissions_check",
            "message": f"File permissions are {file_mode}, recommended 600",
            "fix": f"chmod 600 {CRED_PATH}"
        }, indent=2))

    # Load and validate structure
    try:
        with open(CRED_PATH) as f:
            creds = json.load(f)
    except json.JSONDecodeError as e:
        print(json.dumps({
            "status": "error",
            "step": "json_parse",
            "message": f"Invalid JSON: {str(e)}"
        }, indent=2))
        sys.exit(1)

    required = ["api_key", "workspace_id"]
    missing = [k for k in required if not creds.get(k)]
    if missing:
        print(json.dumps({
            "status": "error",
            "step": "field_check",
            "message": f"Missing required fields: {missing}"
        }, indent=2))
        sys.exit(1)

    api_key = creds["api_key"]
    workspace_id = creds["workspace_id"]
    key_preview = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "****"

    # Test API key
    try:
        req = Request(f"{API_BASE}/user", headers={"X-Api-Key": api_key, "Content-Type": "application/json"})
        resp = urlopen(req)
        user = json.loads(resp.read().decode())
        user_name = user.get("name", "unknown")
        user_email = user.get("email", "unknown")
    except HTTPError as e:
        if e.code == 401:
            print(json.dumps({
                "status": "error",
                "step": "api_auth",
                "message": "API key is invalid or expired (401 Unauthorized)",
                "key_preview": key_preview,
                "fix": "Check your API key in Clockify → Profile Settings"
            }, indent=2))
            sys.exit(1)
        else:
            print(json.dumps({
                "status": "error",
                "step": "api_auth",
                "message": f"HTTP {e.code} when testing API key"
            }, indent=2))
            sys.exit(1)
    except URLError as e:
        print(json.dumps({
            "status": "error",
            "step": "network",
            "message": f"Cannot reach Clockify API: {str(e)[:100]}"
        }, indent=2))
        sys.exit(1)

    # Test workspace access
    try:
        req = Request(f"{API_BASE}/workspaces/{workspace_id}", headers={"X-Api-Key": api_key, "Content-Type": "application/json"})
        resp = urlopen(req)
        ws = json.loads(resp.read().decode())
        ws_name = ws.get("name", "unknown")
    except HTTPError as e:
        print(json.dumps({
            "status": "error",
            "step": "workspace_check",
            "message": f"Workspace ID invalid or no access (HTTP {e.code})",
            "fix": "Check workspace ID in Clockify → Workspace Settings"
        }, indent=2))
        sys.exit(1)

    result = {
        "status": "ok",
        "user": user_name,
        "email": user_email,
        "workspace": ws_name,
        "key_preview": key_preview,
        "project_id": "set" if creds.get("project_id") else "not set",
        "timezone": creds.get("timezone", "America/Montevideo (default)")
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
