$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\python.exe'

if (-not (Test-Path $python)) {
    throw 'Python virtual environment not found. Run: python -m venv .venv && pip install -e apps/api[dev]'
}

Push-Location (Join-Path $root 'apps\api')
try {
    $env:PYTHONPATH = 'src'
    & $python -m uvicorn sara_api.main:app --reload --host 127.0.0.1 --port 8000
}
finally {
    Pop-Location
}
