#!/usr/bin/env python3
"""Push time entries to Clockify from a structured JSON file.

Reads credentials from ~/.config/clockify/credentials.json
Input: JSON file with entries array (date, start, end, description, hours)
Output: JSON summary to stdout
"""

import json
import sys
import os
import time
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

CRED_PATH = os.path.expanduser("~/.config/clockify/credentials.json")
API_BASE = "https://api.clockify.me/api/v1"
MAX_RETRIES = 3
RETRY_DELAY = 2

def load_credentials():
    if not os.path.exists(CRED_PATH):
        print(json.dumps({"error": "credentials_missing", "message": f"Credentials file not found at {CRED_PATH}. Create it first."}))
        sys.exit(1)
    with open(CRED_PATH) as f:
        creds = json.load(f)
    required = ["api_key", "workspace_id"]
    missing = [k for k in required if not creds.get(k)]
    if missing:
        print(json.dumps({"error": "credentials_incomplete", "missing_fields": missing}))
        sys.exit(1)
    return creds

def api_request(method, path, api_key, body=None):
    url = f"{API_BASE}{path}"
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    data = json.dumps(body).encode() if body else None
    req = Request(url, data=data, headers=headers, method=method)
    resp = urlopen(req)
    return json.loads(resp.read().decode()) if resp.status == 201 or resp.status == 200 else None

def get_existing_entries(api_key, workspace_id, user_id, date_str):
    start = f"{date_str}T00:00:00Z"
    end = f"{date_str}T23:59:59Z"
    path = f"/workspaces/{workspace_id}/user/{user_id}/time-entries?start={start}&end={end}&page-size=200"
    try:
        return api_request("GET", path, api_key) or []
    except (HTTPError, URLError):
        return []

def get_user_id(api_key):
    try:
        resp = api_request("GET", "/user", api_key)
        return resp["id"]
    except (HTTPError, URLError) as e:
        print(json.dumps({"error": "auth_failed", "message": str(e)}))
        sys.exit(1)

def to_utc(date_str, time_str, tz_offset_hours=-3):
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    utc_dt = dt - timedelta(hours=tz_offset_hours)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def get_tz_offset(tz_name):
    offsets = {
        "America/Montevideo": -3,
        "America/Buenos_Aires": -3,
        "America/Sao_Paulo": -3,
        "America/New_York": -5,
        "America/Chicago": -6,
        "America/Denver": -7,
        "America/Los_Angeles": -8,
        "America/Caracas": -4,
        "UTC": 0,
        "Europe/London": 0,
        "Europe/Berlin": 1,
    }
    return offsets.get(tz_name, -3)

def push_entry(api_key, workspace_id, project_id, entry, tz_offset, user_id):
    date = entry["date"]
    start_utc = to_utc(date, entry["start"], tz_offset)
    end_utc = to_utc(date, entry["end"], tz_offset)
    description = entry["description"]

    body = {
        "start": start_utc,
        "end": end_utc,
        "description": description,
        "billable": True
    }
    if project_id:
        body["projectId"] = project_id

    for attempt in range(MAX_RETRIES):
        try:
            result = api_request("POST", f"/workspaces/{workspace_id}/time-entries", api_key, body)
            return {"status": "ok", "date": date, "description": description[:60], "clockify_id": result.get("id", "unknown")}
        except HTTPError as e:
            if e.code == 429:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            elif e.code == 401:
                return {"status": "error", "date": date, "description": description[:60], "error": "unauthorized_401"}
            elif e.code == 400:
                error_body = e.read().decode() if hasattr(e, 'read') else str(e)
                return {"status": "error", "date": date, "description": description[:60], "error": f"bad_request_400: {error_body[:200]}"}
            else:
                return {"status": "error", "date": date, "description": description[:60], "error": f"http_{e.code}"}
        except URLError as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
                continue
            return {"status": "error", "date": date, "description": description[:60], "error": f"network: {str(e)[:100]}"}
    return {"status": "error", "date": date, "description": description[:60], "error": "max_retries_exceeded"}

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage", "message": "Usage: push_clockify.py <entries.json> [--dry-run]"}))
        sys.exit(1)

    entries_path = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    if not os.path.exists(entries_path):
        print(json.dumps({"error": "file_not_found", "path": entries_path}))
        sys.exit(1)

    with open(entries_path) as f:
        data = json.load(f)

    entries = [e for e in data["entries"] if e.get("description", "").lower() != "lunch break" and e.get("hours", 0) > 0]

    creds = load_credentials()
    api_key = creds["api_key"]
    workspace_id = creds["workspace_id"]
    project_id = creds.get("project_id")
    tz_name = creds.get("timezone", "America/Montevideo")
    tz_offset = get_tz_offset(tz_name)

    if dry_run:
        print(json.dumps({
            "mode": "dry_run",
            "total_entries": len(entries),
            "timezone": tz_name,
            "tz_offset_hours": tz_offset,
            "sample_entries": [
                {
                    "description": e["description"][:60],
                    "date": e["date"],
                    "start_utc": to_utc(e["date"], e["start"], tz_offset),
                    "end_utc": to_utc(e["date"], e["end"], tz_offset),
                }
                for e in entries[:5]
            ]
        }, indent=2))
        return

    user_id = get_user_id(api_key)
    results = []
    ok_count = 0
    fail_count = 0

    for i, entry in enumerate(entries):
        result = push_entry(api_key, workspace_id, project_id, entry, tz_offset, user_id)
        results.append(result)
        if result["status"] == "ok":
            ok_count += 1
        else:
            fail_count += 1
        # brief pause between requests to be kind to the API
        if i < len(entries) - 1:
            time.sleep(0.3)

    summary = {
        "total_processed": len(entries),
        "successful": ok_count,
        "failed": fail_count,
        "failed_entries": [r for r in results if r["status"] != "ok"]
    }
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
