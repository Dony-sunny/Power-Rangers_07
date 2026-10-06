$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
python -m venv .venv --without-pip
if ($LASTEXITCODE -ne 0) { throw 'Python 3.12+ is required.' }
if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv --cache-dir .runtime/uv-cache pip install --python .venv/Scripts/python.exe -r requirements.txt
} else {
    python -m pip --python .venv install -r requirements.txt
}
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
Push-Location frontend
try {
    npm ci --cache ../.runtime/npm-cache --offline=false
    if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' }
} finally { Pop-Location }
& .venv/Scripts/python.exe -m data.seed.network
if ($LASTEXITCODE -ne 0) { throw 'Database initialization failed.' }
& .venv/Scripts/python.exe scripts/make_demo_documents.py
Write-Host 'Ready. Run: python scripts/dev.py'
