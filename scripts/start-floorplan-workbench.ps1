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
if ([string]::IsNullOrWhiteSpace($env:FLOORPLAN_WORKBENCH_DATA_DIR)) {
  $env:FLOORPLAN_WORKBENCH_DATA_DIR = Join-Path $env:LOCALAPPDATA "Born2Thrill\floorplan-workbench"
}
New-Item -ItemType Directory -Path $env:FLOORPLAN_WORKBENCH_DATA_DIR -Force | Out-Null

Write-Host "Floorplan Workbench: http://127.0.0.1:$Port/floorplan-workbench"
Write-Host "Health check: http://127.0.0.1:$Port/api/floorplan-workbench/health"
Write-Host "Approval queue: $env:FLOORPLAN_WORKBENCH_DATA_DIR"
Write-Host "INTERNAL REVIEW - NOT FOR CUSTOMER DELIVERY"
Write-Host "Press Ctrl+C to stop the local server."

& pnpm exec next dev -H 127.0.0.1 -p $Port
exit $LASTEXITCODE
