# Pruebas de CorePulse-IA

Esta carpeta contiene las pruebas específicas del módulo académico de ISY0101.

Cobertura principal:

- routing;
- `REAL_OR_NA`;
- sanitización;
- RAG interno y externo;
- límite de fuentes;
- trazabilidad `[S#]`;
- validación de salida;
- protección de `measured_data` frente al LLM.

Ejecutar:

```powershell
python -m pytest tests/corepulse_ai -q
```
