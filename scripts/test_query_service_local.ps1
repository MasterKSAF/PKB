param(
  [string[]]$PytestArgs = @("-q")
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$serviceDir = Join-Path $repoRoot "backend/query_service"
$venvPython = Join-Path $serviceDir ".venv/Scripts/python.exe"

if (-not (Test-Path -LiteralPath $venvPython)) {
  python -m venv (Join-Path $serviceDir ".venv")
}

& $venvPython -m pip install --disable-pip-version-check --quiet -r (Join-Path $serviceDir "requirements.txt")

Push-Location $serviceDir
try {
  $env:OTEL_SDK_DISABLED = "true"
  & $venvPython -m pytest @PytestArgs
} finally {
  Pop-Location
}
