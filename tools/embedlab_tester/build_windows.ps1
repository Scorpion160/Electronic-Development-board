$ErrorActionPreference = "Stop"

Write-Host "=== Build EmbedLab Board Tester ===" -ForegroundColor Cyan

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

.\.venv\Scripts\python.exe -m PyInstaller `
    --noconfirm `
    --onefile `
    --name "EmbedLab_Board_Tester" `
    --add-data "profiles;profiles" `
    --add-data "tests;tests" `
    --add-data "firmware;firmware" `
    app\main.py

Write-Host "Build terminé : dist\EmbedLab_Board_Tester.exe" -ForegroundColor Green
