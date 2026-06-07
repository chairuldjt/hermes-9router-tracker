# 9Router Quota Tracker

Hermes addon CLI that installs a `/quota` command so a Telegram-connected Hermes agent can read 9Router quota data directly from the dashboard API, without opening a browser.

This repository can also be used as a standalone CLI, but its primary goal is to make `/quota` easy to install into Hermes.

## Features

- Logs in to a 9Router-style dashboard through HTTP API calls
- Fetches provider accounts and per-account quota details
- Produces Telegram-friendly `summary + detail` output
- Groups results by provider
- Supports text and JSON output
- Installs and removes Hermes `quick_commands`
- Registers `/quota` in `telegram.menu_commands`

## Platform Support

Current support status:

- Windows: supported
- Linux: supported
- macOS: expected to work, but not explicitly tested in this repo

Notes:

- The tracker itself is cross-platform and only requires Python 3.10+
- The Hermes installer is written in Python and works on Windows and Linux
- The bundled [install-hermes-quota.ps1](install-hermes-quota.ps1) helper is Windows-only
- The package declares `PyYAML` because Hermes install/uninstall flows edit `config.yaml`

## Requirements

- Python 3.10+
- Access to a compatible 9Router dashboard
- A dashboard password
- Hermes installed on the same machine if your goal is the `/quota` command

## Repository Layout

- [run_tracker.py](run_tracker.py): safe standalone runner for Hermes `exec` commands
- [run_hermes_install.py](run_hermes_install.py): install `/quota` into Hermes without requiring a package install
- [run_hermes_uninstall.py](run_hermes_uninstall.py): remove the installed Hermes command
- [tracker.py](src/hermes_9router_tracker/tracker.py): tracker logic
- [hermes_install.py](src/hermes_9router_tracker/hermes_install.py): Hermes install logic
- [hermes_uninstall.py](src/hermes_9router_tracker/hermes_uninstall.py): Hermes uninstall logic
- [hermes_config.py](src/hermes_9router_tracker/hermes_config.py): Hermes config helpers

## Quick Start

Clone the repository:

```bash
git clone https://github.com/<your-user>/hermes-9router-tracker.git
cd hermes-9router-tracker
```

Create a local `.env` file:

```bash
cp .env.example .env
```

Minimum required values:

```env
ROUTER_QUOTA_BASE_URL=https://your-9router.example.com
ROUTER_QUOTA_PASSWORD=change-me
```

Test the tracker:

```bash
python run_tracker.py --summary-only
```

`run_tracker.py` automatically loads `.env` from the repository root, so manual environment export is optional as long as the file exists.

## Hermes Installation

Two installation flows are supported.

### Option 1: Direct Repo Runner

This is the simplest and safest option. It does not require `pip install -e .`.

Install `/quota` into Hermes:

```bash
python run_hermes_install.py --hermes-bin hermes --command-name quota --description "Check AI Quota" --runner "python \"/path/to/hermes-9router-tracker/run_tracker.py\""
```

Windows example:

```powershell
python run_hermes_install.py --hermes-bin hermes --command-name quota --description "Check AI Quota" --runner "python `"$PWD\run_tracker.py`""
```

Linux example:

```bash
python run_hermes_install.py --hermes-bin hermes --command-name quota --description "Check AI Quota" --runner "python \"/opt/hermes-9router-tracker/run_tracker.py\""
```

What this changes:

- Adds `quick_commands.quota`
- Adds `/quota` to `telegram.menu_commands`

Remove it again:

```bash
python run_hermes_uninstall.py --hermes-bin hermes --command-name quota
```

### Option 2: Package Install

Use this if your Hermes Python environment is managed and has `pip` available.

Install the package:

```bash
python -m pip install -e .
```

Install the Hermes command:

```bash
router-quota-hermes-install --command-name quota
```

Remove it:

```bash
router-quota-hermes-uninstall --command-name quota
```

Notes:

- This is more compact
- Some Hermes environments do not have `pip` available
- If you are unsure, use `Option 1`

## Recommended Installation Flow

Recommended order:

1. Clone the repo on the same machine that runs Hermes
2. Create `.env`
3. Test `python run_tracker.py --summary-only`
4. Install `/quota` with `python run_hermes_install.py ...`
5. Restart Hermes gateway
6. Test `/quota` from Telegram

If `/quota` was previously installed manually and you want a clean state:

1. Run the repo uninstaller
2. Confirm `/quota` is gone from Hermes `config.yaml`
3. Install it again using this repo's installer

## Provider-Specific Commands

You can install additional commands per provider.

Examples:

```bash
python run_hermes_install.py --command-name quota_codex --provider codex --description "Check Codex quota" --runner "python \"/path/to/hermes-9router-tracker/run_tracker.py\""
python run_hermes_install.py --command-name quota_gemini --provider gemini-cli --description "Check Gemini quota" --runner "python \"/path/to/hermes-9router-tracker/run_tracker.py\""
```

You can also call the tracker directly:

```bash
python run_tracker.py --provider codex
python run_tracker.py --provider gemini-cli
```

## Windows Helper Script

For Windows PowerShell:

```powershell
.\install-hermes-quota.ps1 -CommandName quota
```

With gateway restart:

```powershell
.\install-hermes-quota.ps1 -CommandName quota -RestartGateway
```

Notes:

- This helper is Windows-only
- It uses the repo wrapper scripts, not a global package requirement

## Linux Notes

Linux is supported.

Recommended Linux flow:

```bash
git clone https://github.com/<your-user>/hermes-9router-tracker.git
cd hermes-9router-tracker
cp .env.example .env
python run_tracker.py --summary-only
python run_hermes_install.py --hermes-bin hermes --command-name quota --description "Check AI Quota" --runner "python \"$(pwd)/run_tracker.py\""
hermes gateway restart
```

Linux-specific notes:

- The installer works because it only edits the Hermes `config.yaml`
- If Hermes gateway runs as a user service or systemd service, `hermes gateway restart` is usually enough
- Make sure the `python` binary in the stored runner command is available in the Hermes service PATH

If your service PATH does not resolve `python`, use an absolute interpreter path:

```bash
python run_hermes_install.py --runner "/usr/bin/python3 \"/opt/hermes-9router-tracker/run_tracker.py\""
```

## Environment Variables

Copy [.env.example](.env.example) to `.env`.

Primary variables:

- `ROUTER_QUOTA_BASE_URL`
- `ROUTER_QUOTA_PASSWORD`
- `ROUTER_QUOTA_TIMEOUT`
- `ROUTER_QUOTA_PAGE_SIZE`
- `ROUTER_QUOTA_PROVIDER`

Compatibility note:

- Legacy `AI_ITOPS_*` variables are still accepted as a fallback
- New documentation uses `ROUTER_QUOTA_*` to keep the repo generic and reusable

Optional overrides for non-standard 9Router setups:

- `TRACKER_PROVIDER_ORDER`
  Example: `codex,antigravity,gemini-cli`
- `TRACKER_PROVIDER_LABEL_ORDER`
  JSON object used to define per-provider quota/model ordering
- `TRACKER_LABEL_REPLACEMENTS`
  JSON object used to rename raw API labels
- `TRACKER_PROVIDER_ICONS`
  JSON object used to override provider icons

## CLI Examples

```bash
python run_tracker.py --summary-only
python run_tracker.py --provider codex
python run_tracker.py --format json
python run_tracker.py --base-url https://your-9router.example.com --password "your-password"
```

If the package is installed:

```bash
router-quota-tracker --summary-only
router-quota-tracker --provider codex
router-quota-tracker --format json
```

## Manual Hermes Config Example

If you do not want to use the installer, you can wire it manually:

```yaml
telegram:
  menu_commands:
    quota: Check AI Quota

quick_commands:
  quota:
    type: exec
    command: python "/path/to/hermes-9router-tracker/run_tracker.py"
```

Recommendations:

- Prefer the installer from this repo over manual editing
- Keep secrets in `.env`, not in the command string
- Quote the `run_tracker.py` path if the repo location contains spaces

## Sample Output

```text
📊 AI Quota Tracker
Total account: 12

Summary
- account: 12
- provider: antigravity:3, codex:2, gemini-cli:3, github:1, kiro:3
- low quota:
  kiro | Account 1 example-1@example.com | credit 3.67/50 (7%)
  codex | account-a@example.com | weekly 22/100 (22%)

Detail

🧠 CODEX (2 account)

1. account-a@example.com
   Codex | plan plus | 2 quota
   🟠 weekly
   [██░░░░░░] 78/100 used | remaining 22 (22%)
   ⏳ 2d 5h
```

## Output Modes

- `text`: Telegram-friendly `summary + detail`
- `json`: structured payload for automation

## Development

Run tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Windows PowerShell:

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests -v
```

## GitHub Actions

The included CI workflow:

- tests Python 3.10, 3.11, and 3.12
- runs unit tests
- validates package import

## Security Notes

- Do not commit `.env`
- Do not commit real passwords
- Prefer `.env` or a secret manager for credentials
- Review the target dashboard terms before scraping

## License

MIT
