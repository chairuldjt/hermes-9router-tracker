param(
  [string]$HermesBin = "hermes",
  [string]$CommandName = "quota",
  [string]$Provider = "",
  [string]$Description = "Check AI quota",
  [switch]$RestartGateway
)

$ErrorActionPreference = "Stop"

Write-Host "Installing Hermes /$CommandName quota command..."

$cmd = @(
  "python",
  ".\\run_hermes_install.py",
  "--hermes-bin", $HermesBin,
  "--command-name", $CommandName,
  "--description", $Description,
  "--runner", "python `"$PSScriptRoot\\run_tracker.py`""
)

if ($Provider) {
  $cmd += @("--provider", $Provider)
}

if ($RestartGateway) {
  $cmd += "--restart-gateway"
}

& $cmd[0] $cmd[1..($cmd.Length-1)]
