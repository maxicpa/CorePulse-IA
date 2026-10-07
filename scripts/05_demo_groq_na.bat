@echo off
setlocal
cd /d "%~dp0.."
py -3.12 tools\corepulse_ai_cli.py --provider groq --query "Analiza el uso de CPU. Si no existe temperatura real, no la inventes." --telemetry examples\corepulse_ai\telemetry_cpu_na.json --evidence evidence\demo_llm_real_na_nuevo.json
pause
