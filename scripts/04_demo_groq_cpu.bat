@echo off
setlocal
cd /d "%~dp0.."
py -3.12 tools\corepulse_ai_cli.py --provider groq --query "Analiza el uso y la temperatura de CPU porque el PC esta funcionando lento." --telemetry examples\corepulse_ai\telemetry_cpu_hot.json --evidence evidence\demo_llm_real_nuevo.json
pause
