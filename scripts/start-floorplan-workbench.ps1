param(
  [ValidateRange(1024, 65535)]
  [int]$Port = 3011
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot

Set-Location -LiteralPath $projectRoot
$env:FLOORPLAN_WORKBENCH_ENABLED = "true"

Write-Host "Floorplan Workbench: http://127.0.0.1:$Port/testlauf"
Write-Host "Press Ctrl+C to stop the local server."

& pnpm exec next dev -p $Port
exit $LASTEXITCODE
