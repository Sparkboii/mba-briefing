#!/usr/bin/env python3
"""
MBA Final Placements Briefing — Email Sender Script
Run inside GitHub Actions after research_briefing.py succeeds.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".config" / "hermes"))
if not HERMES_HOME.exists():
    HERMES_HOME = Path.home() / "AppData" / "Local" / "hermes"

CONTRACT_PATH = HERMES_HOME / "placement-news" / "mba-final-placements-briefing.json"
BRIEF_HTML = HERMES_HOME / "placement-news" / "latest-mba-briefing.html"
GAPI = HERMES_HOME / "skills" / "productivity" / "google-workspace" / "scripts" / "google_api.py"
IST = ZoneInfo("Asia/Kolkata")


def load_contract() -> dict:
    if not CONTRACT_PATH.exists():
        sys.exit(f"Contract not found at {CONTRACT_PATH}")
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def save_contract(contract: dict) -> None:
    CONTRACT_PATH.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    now = datetime.now(IST)
    today = now.date().isoformat()

    contract = load_contract()
    delivery = contract.get("delivery", {})
    state = contract.get("state", {})
    recipients = delivery.get("recipients", [])
    cutoff = state.get("last_cutoff")

    if not delivery.get("email_enabled"):
        sys.exit("email delivery is disabled")
    if not recipients or not all(isinstance(x, str) and "@" in x for x in recipients):
        sys.exit("no valid recipients configured")
    if not cutoff or not cutoff.startswith(today):
        sys.exit(f"research state is not fresh for {today}; last_cutoff={cutoff!r}")
    if state.get("last_email_sent") == today:
        print(f"Already sent email for {today}, skipping")
        return 0

    if not BRIEF_HTML.exists():
        sys.exit(f"briefing HTML missing: {BRIEF_HTML}")

    html = BRIEF_HTML.read_text(encoding="utf-8").strip()
    if len(html) < 1000 or "MBA Final" not in html or "Briefing" not in html:
        sys.exit("briefing HTML failed freshness/content sanity check")

    subject = f"MBA Final Placements Briefing — {now.strftime('%d %B %Y')}"

    if dry_run:
        print(json.dumps({"status": "dry_run_ok", "recipients": recipients, "subject": subject, "html_chars": len(html)}))
        return 0

    # Write client secret from secret
    client_secret_path = HERMES_HOME / "google_client_secret.json"
    client_secret = os.environ.get("GMAIL_CLIENT_SECRET")
    if not client_secret:
        sys.exit("GMAIL_CLIENT_SECRET env var not set")
    client_secret_path.write_text(client_secret, encoding="utf-8")

    # Write refresh token from secret
    token_path = HERMES_HOME / "google_token.json"
    refresh_token = os.environ.get("GMAIL_REFRESH_TOKEN")
    if not refresh_token:
        sys.exit("GMAIL_REFRESH_TOKEN env var not set")
    token_path.write_text(refresh_token, encoding="utf-8")

    command = [
        sys.executable, str(GAPI), "gmail", "send",
        "--to", ",".join(recipients),
        "--subject", subject,
        "--body", html,
        "--html",
    ]
    env = os.environ.copy()
    env["HERMES_HOME"] = str(HERMES_HOME)
    result = subprocess.run(command, capture_output=True, text=True, env=env, encoding="utf-8")
    if result.returncode != 0:
        sys.exit(f"Gmail send failed: {result.stderr.strip() or result.stdout.strip()}")

    try:
        sent = json.loads(result.stdout)
    except json.JSONDecodeError:
        sys.exit(f"unexpected Gmail response: {result.stdout.strip()}")

    if sent.get("status") != "sent" or not sent.get("id"):
        sys.exit(f"Gmail did not confirm send: {sent}")

    state["last_email_sent"] = today
    state["last_email_message_id"] = sent["id"]
    contract["state"] = state
    save_contract(contract)

    print(json.dumps({"status": "sent", "recipients": recipients, "subject": subject, "id": sent["id"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())