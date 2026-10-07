# Pruebas y evidencias

## Evidencia real

- `evidence/demo_llm_real.json`: ejecución Groq real del 06/10/2026 con CPU 96 %, 94 °C y RAM 72 %.
- `evidence/demo_llm_real_na.json`: ejecución Groq real del 06/10/2026 con temperatura CPU `N/A`.

Ambas terminaron con `provider.real_llm = true` y `validation.valid = true`. La evidencia N/A conserva el dato sin inventarlo.

## Evidencia determinista

`evidence/dry_run/` se genera con `MockProvider` para todas las rutas. Sirve para comprobar routing, RAG, estructura y trazabilidad de forma reproducible; no reemplaza la demostración con LLM real.

## Pruebas

```powershell
python -m pytest -q
python tools\isy0101_self_check.py
```

La salida exacta de la ejecución incluida en el ZIP se conserva en `evidence/pruebas/pytest.txt` y `self_check.txt`.
