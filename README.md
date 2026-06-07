# 9Router Quota Tracker

Open-source CLI for scraping quota and usage data from a 9Router-style dashboard without opening a browser.

This project was extracted from a Hermes-based Telegram workflow and packaged as a standalone Python tool so it can be reused outside Hermes.

## Features

- Login via HTTP API, no browser automation
- Fetch all provider accounts and quota details
- Telegram-friendly `summary + detail` output
- Group output by provider for easier reading
- Supports plain text and JSON output
- No third-party dependencies required

## Requirements

- Python 3.10+
- Access to a compatible 9Router dashboard
- Dashboard password via environment variable or CLI flag

## Quick Start

```bash
git clone https://github.com/<your-user>/hermes-9router-tracker.git
cd hermes-9router-tracker
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
router-quota-tracker --password "your-password"
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
router-quota-tracker --password "your-password"
```

## Environment Variables

Copy `.env.example` and set values through your shell or deployment environment.

Required or commonly used:

- `AI_ITOPS_URL`
- `AI_ITOPS_PASSWORD`
- `AI_ITOPS_TIMEOUT`
- `AI_ITOPS_PAGE_SIZE`
- `AI_ITOPS_PROVIDER`

Optional formatting overrides for non-standard 9Router installs:

- `TRACKER_PROVIDER_ORDER`
  Example: `codex,antigravity,gemini-cli`
- `TRACKER_PROVIDER_LABEL_ORDER`
  JSON object per provider, used when you want a custom per-model order
- `TRACKER_LABEL_REPLACEMENTS`
  JSON object to rename raw quota labels into friendlier labels
- `TRACKER_PROVIDER_ICONS`
  JSON object to override provider icons

## Example Commands

```bash
router-quota-tracker --password "your-password"
router-quota-tracker --provider codex
router-quota-tracker --format json
router-quota-tracker --summary-only
router-quota-tracker --base-url https://your-9router.example.com --password "your-password"
```

## Sample Output

```text
📊 AI Quota Tracker
Total account: 12

Summary
- account: 12
- provider: codex:2, antigravity:3, gemini-cli:3, github:1, kiro:3
- low quota:
  kiro | Account 1 example-1@example.com | credit 3.67/50 (7%)
  codex | account-a@example.com | weekly 22/100 (22%)

Detail

🧠 CODEX (2 account)

1. account-a@example.com
   Codex | plan plus | 2 quota
   🟠 weekly
   [██░░░░░░] 78/100 used | sisa 22 (22%)
   reset 11 Jun 01:11 UTC
```

## Hermes-First Usage

If your real goal is to expose `/quota` inside Hermes, use the installer command included in this project.

After installing the package:

```bash
router-quota-hermes-install --command-name quota --restart-gateway
```

That will:

- register `quick_commands.quota`
- add `/quota` to `telegram.menu_commands`
- optionally restart Hermes gateway

### Uninstall from Hermes

```bash
router-quota-hermes-uninstall --command-name quota --restart-gateway
```

That will:

- remove `quick_commands.quota`
- remove `/quota` from `telegram.menu_commands`
- optionally restart Hermes gateway

### Install a provider-specific command

```bash
router-quota-hermes-install --command-name quota_codex --provider codex --description "Check Codex quota"
router-quota-hermes-install --command-name quota_gemini --provider gemini-cli --description "Check Gemini quota"
```

### Windows helper script

For Windows PowerShell, this repo also ships a helper script:

```powershell
.\install-hermes-quota.ps1 -CommandName quota -RestartGateway
```

### What Hermes runs

By default the installer wires Hermes to this executable:

```text
router-quota-tracker
```

If you prefer a custom runner path:

```bash
router-quota-hermes-install --runner "python E:\\project\\web\\hermes-9router-tracker\\src\\hermes_9router_tracker\\__main__.py"
```

## Install in Hermes

There are two practical ways to use this project with Hermes.

### Option 1: External helper command

Clone the repository anywhere on the same machine, then call it from a Hermes quick command.

Example `config.yaml` snippet:

```yaml
quick_commands:
  quota:
    type: exec
    command: python E:\project\web\hermes-9router-tracker\src\hermes_9router_tracker\__main__.py --password "your-password"
```

Or with environment variables:

```yaml
quick_commands:
  quota:
    type: exec
    command: python E:\project\web\hermes-9router-tracker\src\hermes_9router_tracker\__main__.py
```

Then set these in the Hermes environment:

```bash
AI_ITOPS_URL=https://your-9router.example.com
AI_ITOPS_PASSWORD=your-password
```

### Option 2: Editable install into Hermes host Python

If the Hermes machine has a Python environment you manage yourself:

```bash
cd E:\project\web\hermes-9router-tracker
python -m pip install -e .
router-quota-tracker --summary-only
```

Then your Hermes quick command can be shorter:

```yaml
quick_commands:
  quota:
    type: exec
    command: router-quota-tracker
```

### Recommended Hermes flow

- Keep the tracker in a separate repository.
- Use Hermes `quick_commands` with `type: exec`.
- Put credentials in environment variables, not directly in the command.
- Restart Hermes gateway after changing command menus.
## Output Modes

- `text`: Telegram-friendly report with summary and grouped details
- `json`: Raw structured data for automation or further processing

## Development

Run tests:

```bash
python -m unittest discover -s tests -v
```

## GitHub Actions

This repository includes a CI workflow that:

- installs Python 3.10, 3.11, and 3.12
- runs unit tests
- validates the package imports correctly

## Security Notes

- Do not commit real passwords.
- Prefer environment variables or CI secrets.
- Review the target dashboard's terms before scraping.

## License

MIT






