$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\python.exe'

Write-Host '== backend tests ==' -ForegroundColor Cyan
Push-Location (Join-Path $root 'apps\api')
try {
    $env:PYTHONPATH = 'src'
    & $python -m pytest -q -p no:cacheprovider
}
finally {
    Pop-Location
}

Write-Host '== frontend tests ==' -ForegroundColor Cyan
Push-Location (Join-Path $root 'apps\web')
try {
    & pnpm test:unit
    & pnpm typecheck
}
finally {
    Pop-Location
}
