# Validación final de la entrega

Fecha de cierre técnico: 07/10/2026.

- `python -m pytest -q`: **32 passed**.
- `python tools/isy0101_self_check.py`: **RESULTADO: PASS**.
- Cobertura de routing: `cpu`, `gpu`, `memory`, `storage`, `network`, `system`, `general`.
- Evidencia real Groq CPU 96 % / 94 °C / RAM 72 %: `validation.valid = true`.
- Evidencia real `REAL_OR_NA`: `cpu_temperature = N/A` y `validation.valid = true`.
- Revisión de secretos: no se incluye ninguna API key real ni archivo `.env`.
- Aislamiento de pruebas Windows: `COREPULSE_AI_ENV_FILE` evita leer/escribir la credencial real del usuario en Credential Manager.
