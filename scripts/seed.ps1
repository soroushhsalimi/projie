$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\python.exe'

Push-Location (Join-Path $root 'apps\api')
try {
    $env:PYTHONPATH = 'src'
    & $python -m sara_api.db.seed
}
finally {
    Pop-Location
}
