# Runs all three services locally WITHOUT Docker (3 windows).
# Prereq: .venv created and filled:  pip install -r <each service>/requirements.txt
# Usage:  powershell -ExecutionPolicy Bypass -File scripts\run_local.ps1
$root = Split-Path $PSScriptRoot -Parent
$py = Join-Path $root ".venv\Scripts\python.exe"

Start-Process powershell -ArgumentList "-NoExit", "-Command",
  "cd '$root\services\mcp-tools-server'; & '$py' server.py"
Start-Process powershell -ArgumentList "-NoExit", "-Command",
  "cd '$root\services\rag-service'; & '$py' -m uvicorn app.main:app --port 8001"
Start-Process powershell -ArgumentList "-NoExit", "-Command",
  "cd '$root\services\agent-service'; & '$py' -m uvicorn app.main:app --port 8000"

Write-Host "mcp-tools :8100 | rag-service :8001 | agent-service :8000"
Write-Host "Try it:  http://localhost:8000/docs"
