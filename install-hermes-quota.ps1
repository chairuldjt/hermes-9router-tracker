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
  "router-quota-hermes-install",
  "--hermes-bin", $HermesBin,
  "--command-name", $CommandName,
  "--description", $Description
)

if ($Provider) {
  $cmd += @("--provider", $Provider)
}

if ($RestartGateway) {
  $cmd += "--restart-gateway"
}

& $cmd[0] $cmd[1..($cmd.Length-1)]
