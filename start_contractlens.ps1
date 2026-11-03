$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root ".venv\Scripts\python.exe"
$streamlit = Join-Path $root ".venv\Scripts\streamlit.exe"

Write-Host "Starting ContractLens backend..."
Start-Process -FilePath $python -ArgumentList "-m", "uvicorn", "backend.main:app", "--reload", "--port", "8000" -WorkingDirectory $root -NoNewWindow

Write-Host "Starting ContractLens frontend..."
Start-Process -FilePath $streamlit -ArgumentList "run", "frontend/app.py", "--server.port", "8501" -WorkingDirectory $root -NoNewWindow

Write-Host ""
Write-Host "Backend: http://127.0.0.1:8000/docs"
Write-Host "Frontend: http://127.0.0.1:8501"
Write-Host ""
Write-Host "If either service fails, run the commands manually from the project root:"
Write-Host "  .\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000"
Write-Host "  .\.venv\Scripts\streamlit run frontend/app.py --server.port 8501"
