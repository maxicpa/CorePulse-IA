@echo off
setlocal
cd /d "%~dp0.."
py -3.12 tools\corepulse_ai_cli.py --provider mock --query "Analiza el uso y la temperatura de CPU." --telemetry examples\corepulse_ai\telemetry_cpu_hot.json
pause
