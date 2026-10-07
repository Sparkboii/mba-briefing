# MBA Final Placements Briefing — GitHub Actions Deployment

This repository contains everything needed to run the **MBA Final Placements Briefing** daily via GitHub Actions (free, cloud-based, no laptop required).

## Architecture

- **Research job** (08:00 IST): Uses Hermes CLI with `competitor-news-monitor` skill to gather, deduplicate, and render a formatted HTML briefing
- **Send job** (08:05 IST): Sends the HTML email via Gmail API to configured recipients

## Required GitHub Secrets

Add these in your repository settings → **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Value | How to get |
|--------|-------|------------|
| `GMAIL_CLIENT_SECRET` | Full JSON content of `google_client_secret.json` | Copy from `C:/Users/Sparsh Pc/AppData/Local/hermes/google_client_secret.json` |
| `GMAIL_REFRESH_TOKEN` | The `refresh_token` value from `google_token.json` | Copy the `refresh_token` field from `C:/Users/Sparsh Pc/AppData/Local/hermes/google_token.json` |

**Example GMAIL_CLIENT_SECRET:**
```json
{
  "installed": {
    "client_id": "160334641879-mcg1ndurutppdjt44ld338ecnf9pl1et.apps.googleusercontent.com",
    "project_id": "serious-case-459315-i4",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "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",
    "redirect_uris": ["http://localhost"]
  }
}
```

**Example GMAIL_REFRESH_TOKEN:**
```
1//0gM2-CoKchhIQCgYIARAAGBASNwF-L9Irfv-xV_I-llt15d7f31R4213s4IB0PJSMS3uMHRxG-0lw7bifvMMKPZqHoOZg-tStWUQ
```

## Recipients

The daily email goes to the email ids that have been entered as recipients.

To change recipients, edit `contract/mba-final-placements-briefing.json` and push.

## Schedule

- **Runs daily at 08:00 IST** (02:30 UTC)
- **Manual trigger**: Available via Actions tab → "Run workflow"

## Local Development

```bash
# Install Hermes
pip install hermes-agent

# Run research locally
HERMES_HOME=/path/to/hermes-home python scripts/research_briefing.py

# Test send (dry run)
HERMES_HOME=/path/to/hermes-home python scripts/send_briefing.py --dry-run
```

## Files

```
├── .github/workflows/mba-briefing.yml   # GitHub Actions workflow
├── contract/
│   ├── mba-final-placements-briefing.json  # Configuration + state
│   └── latest-mba-briefing.html            # Template HTML
├── scripts/
│   ├── research_briefing.py        # Research & render step
│   └── send_briefing.py            # Email send step
├── google-workspace/scripts/       # Google API helpers (copied from Hermes skill)
│   ├── google_api.py
│   ├── _hermes_home.py
│   └── setup.py
└── README.md                       # This file
```

## How It Works

1. **Research step** invokes `hermes run --prompt ... --skills competitor-news-monitor` which:
   - Reads the contract (coverage topics, source policy, format)
   - Searches web for new developments since `state.last_cutoff`
   - Extracts content from primary sources
   - Renders `latest-mba-briefing.html` with navy hero, executive summary, impact maps
   - Updates contract `state.last_cutoff`, `state.seen_event_urls`, `state.last_successful_run`

2. **Send step** (only if research succeeded):
   - Reads the generated HTML and updated contract
   - Writes OAuth credentials from GitHub Secrets to temp files
   - Calls `google_api.py gmail send` with HTML body
   - Updates contract `state.last_email_sent` and `state.last_email_message_id`

## Monitoring

- Check **Actions** tab for run history
- Green = success, Red = failure (check logs)
- Artifacts: `mba-briefing-html` (rendered email), `mba-contract` (state after research), `mba-contract-final` (state after send)

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "GMAIL_CLIENT_SECRET not set" | Add secret in repo settings |
| "Token invalid / refresh failed" | Re-auth locally: `python google-workspace/scripts/setup.py --auth-url` → visit URL → paste code → `--auth-code CODE` → copy new `refresh_token` to secret |
| "Research timeout" | Check Actions logs; may need to increase `timeout-minutes` |
| "No new items found" | Normal if no material news; contract `last_cutoff` still advances |


