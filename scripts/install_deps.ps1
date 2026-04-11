# Run from repo root:  powershell -ExecutionPolicy Bypass -File scripts/install_deps.ps1
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
Write-Host "Installing Python dependencies..."
py -3 -m pip install -r requirements.txt
Write-Host "Installing frontend dependencies..."
Set-Location "$Root\frontend"
npm install
Write-Host "Done. Start API: py -3 -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000"
Write-Host "Start UI:    cd frontend; npm run dev"
