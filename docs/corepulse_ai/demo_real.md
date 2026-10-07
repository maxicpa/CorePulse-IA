# Demo con LLM real

La entrega incluye dos ejecuciones reales ya registradas en `evidence/`. `MockProvider` se usa solo para pruebas deterministas y no reemplaza la evidencia con un LLM real.

## Configuración Groq

La credencial nunca se sube a Git. Puede definirse en el entorno o en un `.env` local ignorado por Git:

```text
GROQ_API_KEY=...
GROQ_MODEL=openai/gpt-oss-120b
```

## Caso CPU reproducible

```powershell
py -3.12 tools\corepulse_ai_cli.py `
  --provider groq `
  --query "Analiza el uso y la temperatura de CPU porque el PC esta funcionando lento." `
  --telemetry examples\corepulse_ai\telemetry_cpu_hot.json `
  --evidence evidence\demo_llm_real_nuevo.json
```

## Caso REAL_OR_NA

```powershell
py -3.12 tools\corepulse_ai_cli.py `
  --provider groq `
  --query "Analiza el uso de CPU. Si no existe temperatura real, no la inventes." `
  --telemetry examples\corepulse_ai\telemetry_cpu_na.json `
  --evidence evidence\demo_llm_real_na_nuevo.json
```

## Evidence gate

`CorePulseAIPipeline.save_evidence()` exige `provider.real_llm = true` y `validation.valid = true`. Una respuesta que invente un estado para una métrica `N/A`, use referencias inexistentes o rompa el contrato no se acepta como evidencia final.

`--live` existe para la integración con el proyecto CorePulse completo; el repositorio académico aislado usa los JSON de `examples/corepulse_ai/`.
