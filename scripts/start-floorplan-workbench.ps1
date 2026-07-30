param(
  [ValidateRange(1024, 65535)]
  [int]$Port = 3011
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot

Set-Location -LiteralPath $projectRoot
$env:FLOORPLAN_WORKBENCH_ENABLED = "true"
if ([string]::IsNullOrWhiteSpace($env:FLOORPLAN_WORKBENCH_DATA_DIR)) {
  $env:FLOORPLAN_WORKBENCH_DATA_DIR = Join-Path $env:LOCALAPPDATA "Born2Thrill\floorplan-workbench"
}
New-Item -ItemType Directory -Path $env:FLOORPLAN_WORKBENCH_DATA_DIR -Force | Out-Null

Write-Host "Floorplan Workbench: http://127.0.0.1:$Port/testlauf"
Write-Host "Approval queue: $env:FLOORPLAN_WORKBENCH_DATA_DIR"
Write-Host "Press Ctrl+C to stop the local server."

& pnpm exec next dev -p $Port
exit $LASTEXITCODE
