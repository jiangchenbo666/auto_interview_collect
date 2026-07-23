@echo off
cd /d "%~dp0"
python -m src.main daily --limit 3 --dry-run --output data/exports/today.md
pause
