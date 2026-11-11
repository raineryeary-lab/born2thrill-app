param(
  [ValidateRange(1024, 65535)]
  [int]$Port = 3020
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot

Set-Location -LiteralPath $projectRoot
$envFile = Join-Path $projectRoot ".env.local"
if (Test-Path -LiteralPath $envFile) {
  foreach ($line in Get-Content -LiteralPath $envFile) {
    $trimmed = $line.Trim()
    if (-not $trimmed -or $trimmed.StartsWith("#") -or -not $trimmed.Contains("=")) {
      continue
    }
    $name, $value = $trimmed.Split("=", 2)
    [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim().Trim('"'), "Process")
  }
}
$env:FLOORPLAN_WORKBENCH_ENABLED = "true"
# Nicht raten. Codex, 2026-08-21, zweiter Durchgang: ein stiller Rueckfall auf
# %LOCALAPPDATA% haette eine DRITTE Datenwurzel angelegt UND die Variable fuer
# den Rest des Prozesses (also auch fuer jede Route, die sie danach liest) so
# aussehen lassen, als sei sie korrekt gesetzt -- genau die Fail-closed-Regel
# umgangen, die heute ueberall sonst eingebaut wurde. Ein fehlendes/kaputtes
# .env.local soll den Start verweigern, nicht eine neue leere Wurzel erfinden.
if ([string]::IsNullOrWhiteSpace($env:FLOORPLAN_WORKBENCH_DATA_DIR)) {
  Write-Error "FLOORPLAN_WORKBENCH_DATA_DIR ist nicht gesetzt (.env.local fehlt oder ist unvollstaendig)."
  exit 1
}
New-Item -ItemType Directory -Path $env:FLOORPLAN_WORKBENCH_DATA_DIR -Force | Out-Null

Write-Host "Floorplan Workbench: http://127.0.0.1:$Port/floorplan-workbench"
Write-Host "Health check: http://127.0.0.1:$Port/api/floorplan-workbench/health"
Write-Host "Approval queue: $env:FLOORPLAN_WORKBENCH_DATA_DIR"
Write-Host "INTERNAL REVIEW - NOT FOR CUSTOMER DELIVERY"
Write-Host "Press Ctrl+C to stop the local server."

# pnpm is not installed on every machine that runs this (it is not here), and
# `& pnpm ...` fails with a bare command-not-found that reads like the server
# crashed. Use whichever runner actually exists.
$runner = if (Get-Command pnpm -ErrorAction SilentlyContinue) { "pnpm" } else { "npx" }
Write-Host "Runner: $runner"
if ($runner -eq "pnpm") {
  & pnpm exec next dev -H 127.0.0.1 -p $Port
} else {
  & npx next dev -H 127.0.0.1 -p $Port
}
exit $LASTEXITCODE
